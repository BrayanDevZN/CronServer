# Camada de infraestrutura

## Objetivo

A infraestrutura implementa o acesso aos recursos externos do sistema. Ela lê configurações, cria conexões com PostgreSQL, Redis e Celery, prepara as tabelas, restaura o schedule no Redis e executa as requisições HTTP cadastradas.

## Estrutura

```text
src/infra/
├── manage.py
├── core/settings.py
├── connect/
│   ├── db.py
│   ├── redis.py
│   └── celery.py
├── migration/
│   ├── db.py
│   └── redis.py
└── requests/request.py
```

## Configuração de ambiente

### `ConfigEnviroin`

`core/settings.py` procura um arquivo `.env` no mesmo diretório do módulo. Se o arquivo existir, usa `python-dotenv` para carregá-lo. Depois exige todas estas variáveis:

| Variável | Uso |
| --- | --- |
| `url` | URL completa de conexão SQLAlchemy com PostgreSQL. |
| `redis_port` | Porta do Redis. No Compose, `6379`. |
| `redis_host` | Host do Redis. No Compose, o nome do serviço `redis`. |
| `sing` | Segredo usado para assinar e validar JWT. |
| `rate_limit` | Limite individual usado pelo middleware. |
| `global_rate_limit` | Limite global usado pelo middleware. |
| `origin` | Origem configurada no CORS. |

`get()` devolve um dicionário com valores textuais. Se qualquer variável estiver ausente, lança `NotFoundEnviroin` durante a importação da infraestrutura.

No Docker Compose, `env_file` injeta o arquivo e `environment` sobrescreve especificamente host e porta do Redis para usar a rede interna.

## Conexão com PostgreSQL

### `ConnectDb`

O objeto recebe uma URL e executa:

1. `_engine()`: chama `sqlalchemy.create_engine()`;
2. `_test()`: abre uma transação e executa `SELECT 1`;
3. `run()`: retorna a `Engine` pronta para uso.

A engine é síncrona. Embora vários métodos de repositório sejam declarados `async`, as operações de SQLAlchemy usadas por eles bloqueiam a thread durante a consulta.

Erros são registrados pelo logger `infra_connect_db`. Existe a exceção `ConnectDbError`, mas atualmente alguns blocos apenas instanciam essa exceção em vez de usar `raise`.

## Conexão com Redis

### `RedisConnect`

A conexão usa `redis.Redis` síncrono com `decode_responses=True`. Isso faz strings e hashes serem devolvidos como texto em vez de bytes.

Fluxo de `run()`:

1. cria o cliente com host e porta;
2. executa `PING` para validar a conexão;
3. retorna o cliente compartilhado.

Falhas de conexão são relançadas como `redis.ConnectionError`.

## Conexão com Celery

### `celery_connect`

Cria uma aplicação Celery recebendo duas URLs:

- backend: `redis://<host>:<port>/0`;
- broker: `redis://<host>:<port>/1`.

Usar bancos lógicos diferentes separa o armazenamento de resultados do Celery da fila de mensagens. O sorted set da aplicação é acessado pelo cliente Redis padrão, que usa o banco lógico `0` quando nenhum banco é informado.

Após criar o app, `infra/manage.py` solicita a descoberta de `src.aplication.tasks.task`, onde `execute_task` é registrado.

## Montagem da infraestrutura

### `infra/manage.py`

Esse módulo é executado no momento da importação e cria objetos globais:

```text
ConfigEnviroin.get()
        │
        ├── ConnectDb.run()    ──► engine
        ├── RedisConnect.run() ──► client
        └── celery_connect()   ──► celery_app
```

Ele também exporta `HttpRequest` e funciona como CLI de migração:

```bash
python -m src.infra.manage migration_db
python -m src.infra.manage migration_redis
```

Como as conexões são criadas durante a importação, qualquer processo que importe `infra.manage` exige ambiente completo e serviços acessíveis.

## Migração do PostgreSQL

### `MigrationDb`

A migração cria três tabelas com `CREATE TABLE IF NOT EXISTS`:

#### `requests`

- `id BIGSERIAL PRIMARY KEY`;
- `public_id UUID UNIQUE`, gerado por `uuid_generate_v4()`;
- URL, headers JSONB, body JSONB e método;
- `created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP`.

#### `cron`

- ID próprio;
- `instance_id` referenciando `requests.id`;
- intervalo inteiro;
- data de referência;
- exclusão em cascata quando a request é apagada.

#### `tasks`

- ID próprio;
- referências para request e cron;
- resultado textual;
- data de criação;
- exclusões em cascata.

A classe também cria a extensão `uuid-ossp`. No código atual, a criação das tabelas acontece antes da chamada que cria a extensão. Em um banco novo sem a extensão, a tabela `requests` pode falhar ao referenciar `uuid_generate_v4()` antes de `_uuid_extension()` ser executado.

## Migração do Redis

### `MigrationRedis`

Essa migração sincroniza os agendamentos persistidos com o sorted set `schedule` na inicialização:

1. `_del()` remove a chave `schedule` existente;
2. `_query()` consulta IDs e intervalos no PostgreSQL;
3. `_exists()` determina se há resultado;
4. `_save()` usa uma pipeline para executar `ZADD schedule`.

Representação esperada:

```text
schedule
├── member: "6"  score: 1
└── member: "7"  score: 2
```

O member é o `requests.id`; o score é o intervalo em dias. O score ordena os itens, mas não representa diretamente um timestamp de próxima execução. O loop consulta o `created_at` no PostgreSQL para tomar essa decisão.

Limitação atual importante: `_query()` usa `fetchone()`, então somente um agendamento é restaurado. Para reconstruir todo o schedule, o resultado precisaria conter todas as linhas e `_save()` precisaria montar o mapping completo.

## Cliente de requisições HTTP

### `HttpRequest`

A classe em `requests/request.py` recebe URL, método, headers e body.

`_validate()` exige URL não vazia e método pertencente a `GET`, `POST`, `PUT`, `PATCH` ou `DELETE`. `_request()` chama:

```python
requests.request(
    method=self.method,
    url=self.url,
    headers=self.headers,
    json=self.body,
)
```

`run()` valida, executa e devolve `response.json()`. Portanto, uma resposta HTTP válida cujo corpo não seja JSON gera uma exceção ao tentar decodificá-la. Também não existe timeout configurado no momento.

Erros da biblioteca Requests são convertidos em `HttpRequestError`. Erros de decodificação JSON não são capturados especificamente por `_request()`, mas acabam sendo tratados pelas tentativas de `ExecuteTask`.

## Dependências da camada

- SQLAlchemy e psycopg2 para PostgreSQL;
- redis-py para Redis;
- Celery para fila e workers;
- Requests para chamadas HTTP;
- python-dotenv para ambiente;
- camada de logs para observabilidade.

## Pontos operacionais

- O PostgreSQL pode ser externo; somente a URL configurada importa para a aplicação.
- O Redis do Compose não possui volume declarado. Reiniciar o mesmo contêiner pode preservar seu filesystem gravável; recriar o contêiner elimina esse estado.
- A migração Redis limpa `schedule` antes de reconstruí-lo, mas não limpa caches de requests, tasks ou rate limits.
- Migrações são serviços separados no Compose e terminam depois da execução.
- Secrets e URLs de banco não devem ser incluídos na documentação nem versionados.
