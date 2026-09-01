# Camada de repositório

## Objetivo

A camada de repositório concentra a persistência e esconde da aplicação os detalhes de SQL e Redis. Ela é dividida em três partes:

- `db`: comandos SQL para PostgreSQL;
- `redis`: operações genéricas sobre Redis;
- `control`: coordenação entre banco e cache.

## Estrutura

```text
src/repository/
├── manage.py
├── db/
│   ├── requests.py
│   ├── tasks.py
│   └── all.py
├── redis/
│   └── control.py
└── control/
    ├── requests.py
    ├── tasks.py
    └── all.py
```

## Fachada `ControlDb`

`repository/manage.py` recebe uma engine SQLAlchemy e uma conexão Redis e disponibiliza:

| Atributo | Classe | Uso |
| --- | --- | --- |
| `requests` | `RequestsControl` | CRUD de configurações e schedule. |
| `tasks` | `TasksControl` | Persistência e consulta de execuções. |
| `all` | `AllDbControl` | Consulta agregada de instâncias. |

A camada de serviço cria uma única fachada compartilhada pela API, pelo cron e pelo worker.

## Repositório PostgreSQL de requests

### Inserção

`RequestsDb.insert()` usa uma única transação para:

1. inserir URL, método, headers e body em `requests`;
2. obter o novo `requests.id`;
3. inserir `instance_id` e intervalo em `cron`;
4. combinar os dois mappings retornados.

Como as duas gravações estão dentro de `engine.begin()`, uma falha antes do fim desfaz a transação.

Após a combinação, campos de mesmo nome são sobrescritos pelo segundo dicionário. Em especial, `id` e `created_at` de `cron` podem substituir os valores homônimos de `requests`; o código também depende de `instance_id` para conservar o vínculo interno.

### Seleção

`RequestsDb.select(value, search)` aceita três buscas:

- `public_id` em `requests`;
- `url` em `requests`;
- `id` em `requests`.

A consulta faz `INNER JOIN cron` e cria o alias `cron_id` para distinguir `cron.id`. Retorna apenas a primeira linha.

Formato lógico do retorno:

```json
{
  "id": 7,
  "public_id": "uuid",
  "url": "https://example.com",
  "headers": {},
  "body": {},
  "method": "GET",
  "cron_id": 7,
  "interval": 1,
  "created_at": "timestamp do cron"
}
```

### Atualização

O método trata separadamente:

- `interval`: atualiza `cron.interval` através do `public_id`;
- `created_at`: atualiza `cron.created_at`;
- demais campos: tenta atualizar `requests`.

Os dois primeiros usam parâmetros para os valores. No caminho genérico, o nome da coluna aparece como `:set`. Bancos SQL não tratam identificadores de coluna como parâmetros de valor; esse trecho precisa de uma lista segura de SQLs ou composição controlada para atualizar método, headers e body corretamente.

### Exclusão

Exclui `requests` pelo `public_id`. As foreign keys removem os registros relacionados de `cron` e `tasks` por cascata.

## Controle de requests e cache

### Inserção

`RequestsControl.insert()`:

1. serializa headers e body;
2. chama o repositório SQL;
3. normaliza UUID e timestamp para texto;
4. cria um hash `request:{public_id}` com TTL padrão de sessenta segundos;
5. executa `ZADD schedule <interval> <instance_id>`.

O sorted set não recebe TTL e permanece enquanto a chave existir.

### Seleção

Primeiro tenta uma leitura no Redis; se não encontrar, consulta o PostgreSQL, normaliza o resultado e cria um hash temporário.

Padrões usados atualmente:

| Momento | Chave |
| --- | --- |
| Busca | `request:{search}:{value}` |
| Cache após busca | `request:{value}` |
| Cache após criação | `request:{public_id}` |

Como os padrões diferem, uma busca como `search="id", value=7` procura `request:id:7`, mas grava `request:7`. Na próxima passagem, não encontra a chave recém-gravada e volta ao banco. Esse é o motivo dos logs repetidos de consulta SQL no loop.

### Atualização

Atualiza o banco e apaga somente `request:{public_id}`. Como podem existir caches construídos por ID, URL ou padrões diferentes, há possibilidade de outras chaves permanecerem até o TTL.

Quando o campo atualizado é `interval`, o score correspondente no sorted set não é atualizado atualmente. Assim, o banco pode guardar um intervalo novo enquanto o loop ainda recebe o score anterior do Redis.

### Exclusão

Apaga pelo `public_id`, invalida `request:{public_id}` e executa `ZREM schedule <instance_id>`. O uso do ID interno é necessário porque ele é o member salvo no sorted set.

## Repositório PostgreSQL de tasks

### Inserção

`TasksDb.insert()` usa uma CTE:

1. insere `instance_id`, `cron_id` e `result` em `tasks`;
2. combina a task inserida com `requests` e `cron`;
3. garante no join que cron e task pertencem à mesma instância;
4. devolve um mapping completo para o cache.

### Seleção

Faz join das três tabelas, filtra por `instance_id`, ordena por `tasks.created_at DESC` e usa `fetchone()`. O resultado é a execução mais recente.

### Atualização e exclusão

`update()` altera o resultado de todas as linhas que correspondem ao `instance_id`, embora retorne somente uma linha. `delete()` apaga todas as tasks da instância.

## Controle de tasks e cache

`TasksControl` usa a chave:

```text
task:instance_id:{instance_id}
```

Na inserção ou seleção, normaliza `created_at`, `public_id`, headers e body antes de criar um hash com TTL. Atualizações e exclusões removem a chave.

Como o cache armazena apenas um hash, ele representa a task mais recente, não uma coleção completa do histórico.

## Consulta de todas as instâncias

`AllDb` e `AllDbControl` pretendem obter e cachear todas as instâncias na chave `all_instances`. Essa funcionalidade não aparece nas rotas atuais.

Há problemas conhecidos nesse trecho:

- a SQL em `AllDb.get()` não contém uma cláusula `FROM requests r` válida;
- o método é assíncrono, mas `AllDbControl.get()` chama `self.db.get()` sem `await`;
- `dict(result.mappings().fetchall())` não representa corretamente uma lista arbitrária de registros;
- a chave `all_instances` não é invalidada pelo CRUD de requests.

## Operações genéricas de Redis

### `incr(name, time)`

Usa `WATCH`, `MULTI`, `INCR` e `EXPIRE`. Serve aos contadores de rate limit. O TTL padrão é sessenta segundos.

### `hash(name, data, time)`

Grava um mapping com `HSET` e aplica TTL, também dentro de pipeline transacional.

### `sorted_set(name, data)`

Executa `ZADD` para um ou mais membros. Um membro existente tem seu score atualizado; não é duplicado.

### `sorted_get(name)`

Executa `ZRANGE 0 99 WITHSCORES`. Retorna no máximo cem pares, ordenados do menor para o maior score.

### `get(name)`

Executa Redis `GET`. Esse comando lê strings, não hashes. Como os caches de request e task são criados com `HSET`, a leitura de uma mesma chave por `GET` causaria `WRONGTYPE` se o padrão de chaves coincidisse. Para ler hashes, seria necessário um método baseado em `HGETALL`.

### `delete(name, user=None)`

- sem `user`: executa `DEL name`;
- com `user`: executa `ZREM name user`.

## Modelo de consistência

PostgreSQL é a fonte persistente. Redis contém:

- uma agenda operacional (`schedule`);
- caches temporários;
- contadores de rate limit;
- broker e backend do Celery em bancos lógicos próprios.

A escrita de PostgreSQL e Redis não forma uma única transação distribuída. Se o banco confirmar e o Redis falhar, a migration Redis deve reconstruir o schedule numa inicialização posterior.

## Dependências

- SQLAlchemy `Engine` e `text`;
- cliente Redis síncrono;
- camada de infraestrutura para os objetos concretos, indiretamente pela montagem do serviço;
- camada de logs nos repositórios SQL e Redis.
