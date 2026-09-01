# Camada de aplicação

## Objetivo

A camada de aplicação contém os pontos de entrada do Cron Server e coordena os casos de uso. Ela recebe chamadas HTTP, aplica middleware e dependências, inicia o loop de agendamento e transforma a execução de uma requisição em uma task Celery.

Ela não cria conexões diretamente nem escreve SQL. Para acessar dados e integrações, utiliza os objetos montados pela camada de serviço.

## Estrutura

```text
src/aplication/
├── main.py
├── api/
│   ├── manage.py
│   ├── dependences/depends.py
│   ├── handles/requests.py
│   ├── handles/tasks.py
│   └── midlleware/base.py
├── cron/manage.py
└── tasks/
    ├── execute.py
    └── task.py
```

O nome físico do pacote é `aplication`, com um único `p`, e deve ser usado assim nos imports e comandos.

## Inicialização

### `main.py`

O módulo cria `app = InstanceAPI().run()` no momento da importação. É esse objeto que o Uvicorn carrega por meio de `src.aplication.main:app`.

Quando o arquivo é executado como módulo com o argumento `start_cron`, ele importa `cron_loop` e inicia a coroutine com `asyncio.run()`:

```bash
python -m src.aplication.main start_cron
```

Portanto, o mesmo módulo atende dois processos diferentes:

- importado pelo Uvicorn: fornece a aplicação FastAPI;
- executado com `start_cron`: mantém o scheduler em execução.

## Construção da API

### `InstanceAPI`

A classe localizada em `api/manage.py` monta o FastAPI em três etapas:

1. `_cors()` adiciona `CORSMiddleware` e lê a origem permitida de `envroins["origin"]`;
2. `_mid()` adiciona o middleware próprio de rate limit;
3. `_routes()` registra os routers de requests e tasks.

O método `run()` executa essas etapas e retorna a instância de `FastAPI`.

## Rotas de requests

Todas usam o prefixo `/requests`.

### `POST /requests/`

Cria uma nova requisição agendada.

Corpo esperado:

```json
{
  "url": "https://example.com/job",
  "method": "GET",
  "headers": {},
  "body": {},
  "interval": 1
}
```

Fluxo:

1. Pydantic valida `RequestsModelCreate`.
2. O handler procura a URL existente por `control_db.requests.select(search="url", value=request.url)`.
3. Se encontrar a mesma URL com o mesmo método, retorna `401`.
4. Caso contrário, grava `requests` e `cron` através do repositório.
5. O repositório também cria cache e adiciona o ID ao sorted set `schedule`.
6. `jwt_auth.create()` gera o token com `public_id` e `created_at`.
7. Retorna `201` com `status`, `error` e `token`.

Resposta de sucesso atual:

```json
{
  "error": null,
  "status": "sucess",
  "token": "<jwt>"
}
```

### `GET /requests/{instance_token}`

Decodifica o token presente na URL, procura a instância pelo `public_id` e confirma sua existência. Atualmente, a resposta devolve o próprio token no campo `content`, e não os dados completos do agendamento.

Embora o token esteja no caminho, o middleware também exige `X-instance_token` para requisições que não sejam `POST`.

### `PATCH /requests/`

Exige o header `X-instance_token`. A dependência `DependsIntance.exists` valida o token e fornece a instância completa ao handler.

Corpo esperado:

```json
{
  "set": "interval",
  "value": "2"
}
```

Os campos aceitos pelo schema são `method`, `headers`, `body` e `interval`. O handler passa `public_id`, nome do campo e valor ao repositório.

### `DELETE /requests/`

Exige `X-instance_token`. A dependência combina o payload do JWT com os dados encontrados no banco. O handler usa:

- `payload["public_id"]` para excluir no PostgreSQL;
- `payload["id"]` para remover o membro correspondente do sorted set `schedule`.

As chaves estrangeiras com `ON DELETE CASCADE` removem também `cron` e `tasks` associados.

## Rota de tasks

### `GET /tasks/`

Exige o header `X-instance_token`. Depois que a dependência valida a instância, o handler usa seu `id` interno para buscar a última task registrada. A resposta possui `error` e `content`.

O repositório ordena as tasks por data decrescente, mas usa `fetchone()`. Assim, a rota entrega somente a execução mais recente, apesar do comentário no código mencionar histórico.

## Dependência de autenticação

### `DependsIntance.exists`

A classe em `dependences/depends.py` executa quatro passos:

1. lê `X-instance_token` do request;
2. decodifica o JWT;
3. consulta a requisição pelo `public_id`;
4. combina payload e registro com `self.payload | instance`.

Se não existir uma instância correspondente, lança `HTTPException` com status `401`.

## Middleware de rate limit

`MIdlleware`, em `midlleware/base.py`, intercepta todas as chamadas antes das rotas.

Chaves usadas no Redis:

| Chave | Escopo | Expiração padrão |
| --- | --- | --- |
| `global_rate_limit` | Todas as requisições | 60 segundos |
| `ip?rate_limit:{ip}` | Criação por endereço IP | Depende da chamada de incremento |
| `token?rate_limit: {token}` | Rotas autenticadas | 60 segundos |

O contador global é conferido e incrementado. Para `POST /requests/`, o middleware verifica o IP. Para os demais métodos, exige o token e aplica o limite por token.

## Loop de agendamento

`cron/manage.py` mantém uma coroutine infinita:

1. lê até cem membros do sorted set `schedule`;
2. recebe pares `(instance_id, interval)` ordenados pelo score;
3. busca cada instância pelo ID;
4. converte `created_at` com `datetime.fromisoformat()`;
5. calcula `next_run = created_at + timedelta(days=interval)`;
6. compara o horário com `datetime.now(timezone.utc)`;
7. se estiver vencido, atualiza `cron.created_at`;
8. envia `execute_task.delay(instance)`;
9. aguarda dez segundos antes da próxima leitura.

A atualização do horário ocorre antes do envio ao Celery. Isso impede que a mesma instância seja enviada repetidamente enquanto o worker ainda executa a chamada HTTP.

## Task e worker

### Registro Celery

`tasks/task.py` registra uma task com nome explícito `execute_task`. A função é síncrona para o Celery, instancia `ExecuteTask` e executa sua rotina assíncrona com `asyncio.run()`.

O módulo precisa estar descoberto pelo Celery; `infra/manage.py` chama `autodiscover_tasks(["src.aplication.tasks.task"])`.

### `ExecuteTask`

A classe recebe um dicionário completo da requisição e extrai:

- `id` como `instance_id`;
- `public_id`;
- `cron_id`;
- URL, método, headers e body.

`_request()` converte headers e body de JSON textual para objetos Python quando necessário. Em seguida, usa `HttpRequest`. Em caso de erro, tenta até quatro vezes. Depois da quarta falha, define o resultado como `None`.

`_save()` registra `success` quando houve resposta e `failed` quando todas as tentativas falharam. O retorno da task é `None`; o resultado de negócio fica no PostgreSQL.

## Dependências da camada

```text
Aplicação
├── Serviço: control_db, client e jwt_auth
├── Domínio: schemas recebidos por meio do serviço
├── Infraestrutura: app settings e Celery
├── FastAPI/Starlette
└── asyncio e datetime
```

## Tratamento de erros atual

Os handlers capturam exceções gerais e normalmente retornam status `501`. Erros da dependência usam `401`, e o middleware usa `429` para rate limit. O loop converte falhas em `CronError` e encerra o processo; o Docker não define uma política explícita de restart para o cron.

## Pontos de atenção da implementação atual

- `interval` representa dias, não segundos ou minutos.
- A grafia `sucess` está presente nas respostas e nos testes.
- O cache de requests lê `request:{search}:{value}`, mas grava `request:{value}` após uma consulta; esses padrões ainda não coincidem.
- A criação grava o cache como `request:{public_id}`, outro padrão de chave.
- O middleware compara alguns valores sem conversão explícita para inteiro no limite por IP.
- A atualização dinâmica de colunas SQL precisa ser validada na camada de repositório.
- A task considera sucesso quando `HttpRequest.run()` retorna sem exceção; não existe hoje uma regra específica para códigos HTTP 4xx ou 5xx.
