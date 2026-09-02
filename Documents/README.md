<div align="center">

# Cron Server

### Agendamento distribuído e execução assíncrona de requisições HTTP

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)

![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?style=for-the-badge&logo=fastapi&logoColor=white)

![Celery](https://img.shields.io/badge/Celery-5.6-37814A?style=for-the-badge&logo=celery&logoColor=white)

![Redis](https://img.shields.io/badge/Redis-8-DC382D?style=for-the-badge&logo=redis&logoColor=white)

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)

![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

![Nginx](https://img.shields.io/badge/Nginx-Reverse%20Proxy-009639?style=for-the-badge&logo=nginx&logoColor=white)

![License](https://img.shields.io/badge/Licen%C3%A7a-Uso%20com%20atribui%C3%A7%C3%A3o-6f42c1?style=for-the-badge)

![Arquitetura visual do Cron Server](Documents/assets/cron-server-banner.png)

O **Cron Server** cadastra requisições HTTP, agenda execuções recorrentes, distribui o processamento para workers e mantém o histórico das execuções.

</div>

---

## Sumário

- [Visão geral](#visão-geral)

- [Principais recursos](#principais-recursos)

- [Como a aplicação funciona](#como-a-aplicação-funciona)

- [Arquitetura](#arquitetura)

- [Rotas da API](#rotas-da-api)

- [Autenticação](#autenticação)

- [Agendamento e execução](#agendamento-e-execução)

- [Persistência](#persistência)

- [Redis](#redis)

- [Serviços Docker](#serviços-docker)

- [Configuração](#configuração)

- [Executando a aplicação](#executando-a-aplicação)

- [Testando o fluxo](#testando-o-fluxo)

- [Estrutura do projeto](#estrutura-do-projeto)

- [Logs e observabilidade](#logs-e-observabilidade)

- [Documentação complementar](#documentação-complementar)

- [Estado atual e limitações conhecidas](#estado-atual-e-limitações-conhecidas)

- [Licença](#licença)

## Visão geral

O Cron Server é uma aplicação backend para automatizar chamadas HTTP recorrentes. Um cliente informa a URL de destino, método, headers, body e intervalo. A API persiste a configuração, gera um token de acesso e registra o agendamento no Redis. Um processo de cron verifica periodicamente quais instâncias devem executar e publica uma task no Celery. O worker consome essa task, realiza a chamada HTTP e salva o resultado no PostgreSQL.

O projeto separa a recepção da requisição da execução do trabalho. Assim, a API não precisa permanecer aguardando a URL externa responder e o processamento pode ser distribuído entre workers.

### Exemplo de uso

Uma integração precisa chamar diariamente um endpoint de sincronização:

```json

{

"url": "https://api.example.com/synchronize",

"method": "POST",

"headers": {

"Authorization": "Bearer example-token"

},

"body": {

"scope": "customers"

},

"interval": 1

}

```

O Cron Server armazena essa configuração, retorna um JWT e passa a executar a chamada quando o intervalo é atingido.

> Na implementação atual, `interval` é medido em **dias**.

## Principais recursos

- Cadastro de requisições `GET`, `POST`, `PUT`, `PATCH` e `DELETE`.

- Headers e body configuráveis em JSON.

- Token JWT individual para acessar cada instância.

- Persistência de configurações e execuções no PostgreSQL.

- Schedule operacional armazenado em sorted set do Redis.

- Processamento assíncrono com Celery.

- Tentativas automáticas em caso de falha na chamada externa.

- Rate limit global, por IP e por token.

- Atualização e exclusão de agendamentos.

- Consulta da execução mais recente.

- Inicialização completa com Docker Compose.

- Nginx como reverse proxy na entrada da API.

- Migração do banco e reconstrução do schedule como processos separados.

- Logs por camada, com identificação visual por cores.

## Como a aplicação funciona

### 1. Cadastro

O cliente envia `POST /requests/`. O FastAPI valida o corpo usando Pydantic. Antes de criar o registro, o handler verifica se já existe uma instância com a mesma URL e o mesmo método.

### 2. Persistência

O repositório abre uma transação no PostgreSQL e cria:

- uma linha em `requests`, contendo a chamada HTTP;

- uma linha em `cron`, contendo o vínculo e o intervalo.

Se uma das gravações falhar, a transação não é confirmada parcialmente.

### 3. Registro no schedule

Depois da confirmação no banco, o controle de repositório adiciona ao Redis:

```text

ZADD schedule <interval> <instance_id>

```

O `instance_id` é o ID interno de `requests`, e o score é o intervalo.

### 4. Emissão do token

O domínio cria um JWT assinado com `HS256`. O token contém o `public_id` da instância e a data de criação do agendamento. Esse token é devolvido ao cliente e passa a ser necessário nas operações protegidas.

### 5. Verificação do cron

O processo `cron` consulta o sorted set `schedule` a cada dez segundos. Para cada ID, busca a configuração completa e calcula:

```text

próxima execução = cron.created_at + intervalo em dias

```

Quando o horário atual alcança ou ultrapassa a próxima execução, o cron atualiza `cron.created_at` e publica `execute_task` no broker Celery.

### 6. Processamento pelo worker

O worker recebe o dicionário da instância, prepara headers e body e realiza a chamada com a biblioteca Requests. Em caso de exceção, tenta novamente até completar quatro tentativas.

### 7. Resultado

Ao terminar, o worker grava uma linha em `tasks`:

- `success`: a chamada retornou e o conteúdo foi processado;

- `failed`: todas as tentativas terminaram com erro.

O cliente pode consultar a execução mais recente por `GET /tasks/`.

## Arquitetura

```mermaid

flowchart LR

Client[Cliente] -->|HTTP + JSON| Nginx[Nginx Reverse Proxy]

Nginx -->|proxy_pass| API[FastAPI API]

API -->|configuração| Repo[Repository Control]

Repo -->|persistência| DB[(PostgreSQL)]

Repo -->|cache e schedule| Redis[(Redis)]

Cron[Cron Loop] -->|lê schedule| Redis

Cron -->|busca e atualiza| DB

Cron -->|execute\_task.delay| Broker[Celery Broker]

Broker --> Worker[Celery Worker]

Worker -->|requisição HTTP| Target[URL externa]

Worker -->|salva resultado| DB

Worker -->|atualiza cache| Redis

Client -->|consulta com JWT| API

```

### Responsabilidade das camadas

| Camada | Responsabilidade |

| --- | --- |

| Aplicação | Rotas FastAPI, middleware, dependências, cron e task Celery. |

| Domínio | Schemas Pydantic e autenticação JWT. |

| Serviço | Montagem e disponibilização das dependências compartilhadas. |

| Repositório | SQL, cache, schedule e coordenação PostgreSQL/Redis. |

| Infraestrutura | Ambiente, conexões, migrações e cliente HTTP. |

| Controller | Dockerfiles, dependências e Docker Compose. |

| Logs | Configuração comum de arquivos, console e cores. |

Uma descrição completa de cada camada está disponível em [`Documents/layer/README.md`](Documents/layer/README.md).

## Rotas da API

Base local padrão:

```text

http://localhost:8080

```

### Resumo

| Método | Rota | Autenticação | Descrição |

| --- | --- | --- | --- |

| `POST` | `/requests/` | Não | Cria uma requisição agendada e retorna um token. |

| `GET` | `/requests/{instance_token}` | Header + token na URL | Confirma que a instância existe. |

| `PATCH` | `/requests/` | `X-instance_token` | Atualiza um campo permitido. |

| `DELETE` | `/requests/` | `X-instance_token` | Exclui a instância e seu schedule. |

| `GET` | `/tasks/` | `X-instance_token` | Consulta a execução mais recente da instância. |

### Criar um agendamento

```http

POST /requests/

Content-Type: application/json

```

Corpo:

```json

{

"url": "https://httpbin.org/anything/cron-server",

"method": "GET",

"headers": {

"X-Origin": "cron-server"

},

"body": {},

"interval": 1

}

```

Exemplo com cURL:

```bash

curl --request POST http://localhost:8080/requests/ \

--header "Content-Type: application/json" \

--data '{

"url": "https\://httpbin.org/anything/cron-server",

"method": "GET",

"headers": {"X-Origin": "cron-server"},

"body": {},

"interval": 1

}'

```

Resposta de sucesso:

```json

{

"error": null,

"status": "sucess",

"token": "<instance-token>"

}

```

Status atual: `201 Created`.

Se já existir a mesma URL com o mesmo método, a API retorna `401` e não cria outra instância.

### Consultar uma instância

```http

GET /requests/{instance_token}

X-instance_token: <instance-token>

```

Exemplo:

```bash

curl http://localhost:8080/requests/<instance-token> \

--header "X-instance_token: <instance-token>"

```

Resposta atual:

```json

{

"error": null,

"content": "<instance-token>"

}

```

Essa rota confirma a existência da instância. No comportamento atual, `content` devolve o token recebido, e não a configuração completa.

### Atualizar uma instância

```http

PATCH /requests/

X-instance_token: <instance-token>

Content-Type: application/json

```

Campos aceitos:

- `method`;

- `headers`;

- `body`;

- `interval`.

Exemplo de atualização do intervalo:

```bash

curl --request PATCH http://localhost:8080/requests/ \

--header "X-instance_token: <instance-token>" \

--header "Content-Type: application/json" \

--data '{"set":"interval","value":"2"}'

```

Resposta de sucesso:

```json

{

"status": "sucess",

"error": null

}

```

### Excluir uma instância

```http

DELETE /requests/

X-instance_token: <instance-token>

```

Exemplo:

```bash

curl --request DELETE http://localhost:8080/requests/ \

--header "X-instance_token: <instance-token>"

```

A exclusão remove:

- a linha de `requests`;

- o cron relacionado, por cascata;

- as tasks relacionadas, por cascata;

- o membro correspondente do sorted set `schedule`;

- o cache principal associado ao `public_id`.

### Consultar a última execução

```http

GET /tasks/

X-instance_token: <instance-token>

```

Exemplo:

```bash

curl http://localhost:8080/tasks/ \

--header "X-instance_token: <instance-token>"

```

Quando existe uma execução, `content` contém o registro combinado de request, cron e task. Sem execução, o conteúdo pode ser `null`.

## Autenticação

Cada instância recebe um JWT próprio. Nas rotas protegidas, envie:

```text

X-instance_token: <token>

```

O fluxo de autorização é:

1. o middleware confirma que o header existe;

2. a dependência decodifica o JWT com o segredo configurado;

3. extrai o `public_id`;

4. consulta a instância no repositório;

5. permite a operação somente se o registro ainda existir.

O token atual não possui expiração automática. A exclusão da instância, contudo, torna o token inutilizável porque o `public_id` deixa de existir no banco.

## Agendamento e execução

### Unidade do intervalo

O scheduler usa:

```python

timedelta(days=interval)

```

Portanto:

| `interval` | Frequência atual |

| ---: | --- |

| `1` | Uma vez por dia. |

| `2` | A cada dois dias. |

| `7` | Uma vez por semana. |

### Referência de tempo

`cron.created_at` representa a referência usada para calcular a próxima execução. Ao identificar uma task vencida, o cron atualiza esse campo para o horário UTC atual antes de publicar no Celery. Essa ordem evita envios duplicados enquanto o worker ainda está ocupado.

### Frequência de polling

O loop aguarda dez segundos entre leituras. Isso significa que uma execução pode ser disparada alguns segundos depois do instante exato calculado, dependendo da posição no ciclo.

### Resultado da task

A task Celery retorna `None`. O resultado útil é persistido na tabela `tasks`, pois o MVP considera o banco como histórico de negócio.

## Persistência

### Relacionamentos

```mermaid

erDiagram

requests ||--|| cron : possui

requests ||--o{ tasks : gera

cron ||--o{ tasks : agenda

requests {

    bigint id PK

    uuid public\_id UK

    text url

    jsonb headers

    jsonb body

    text method

    timestamptz created\_at

}

cron {

    bigint id PK

    bigint instance\_id FK

    integer interval

    timestamptz created\_at

}

tasks {

    bigint id PK

    bigint instance\_id FK

    bigint cron\_id FK

    text result

    timestamptz created\_at

}

```

### Identificadores

- `requests.id`: ID interno usado pelo schedule e chamado de `instance_id` nas tabelas relacionadas;

- `requests.public_id`: UUID público guardado no JWT;

- `cron.id`: ID do agendamento, transportado como `cron_id`;

- `tasks.id`: ID de uma execução individual.

As relações possuem `ON DELETE CASCADE`, permitindo que a exclusão de uma request remova seus dados dependentes.

## Redis

O Redis atende três papéis diferentes:

### Schedule

O sorted set `schedule` contém um membro por instância:

```text

member = requests.id

score  = cron.interval

```

Adicionar novamente o mesmo member atualiza seu score em vez de criar duplicata.

### Cache

Hashes temporários armazenam dados de requests e tasks. O TTL padrão dos hashes é sessenta segundos.

### Rate limit

Contadores com expiração controlam o volume global, por IP e por token.

Além disso, o Celery utiliza Redis como broker e backend em bancos lógicos separados.

## Serviços Docker

| Serviço | Processo | Papel |

| --- | --- | --- |

| `redis` | Redis 8 | Schedule, cache, rate limit e suporte ao Celery. |

| `migration_db` | `src.infra.manage migration_db` | Cria extensão e tabelas. |

| `migration_redis` | `src.infra.manage migration_redis` | Reconstrói o sorted set. |

| `api` | Uvicorn | Expõe as rotas FastAPI na porta 8000. |

| `worker` | Celery worker | Executa chamadas HTTP em segundo plano. |

| `cron` | Loop assíncrono | Verifica datas e envia tasks ao broker. |

O PostgreSQL é configurado por URL e pode estar fora do Compose. Dentro da rede Docker, o Redis é acessado pelo hostname `redis`.

## Configuração

Crie `src/infra/core/.env` com as variáveis exigidas:

```dotenv

url=postgresql+psycopg2://USER:PASSWORD@HOST:5432/DATABASE

redis_host=localhost

redis_port=6379

sing=troque-por-um-segredo-forte

rate_limit=100

global_rate_limit=1000

origin=http://localhost:3000

```

No Docker Compose, `redis_host` e `redis_port` são sobrescritos para:

```text

redis_host=redis

redis_port=6379

```

### Recomendações

- não versionar o `.env`;

- usar um segredo JWT longo e aleatório;

- exigir TLS na conexão com banco externo quando disponível;

- limitar a origem CORS em produção;

- não registrar tokens completos em ambientes públicos.

## Executando a aplicação

### Docker Compose

Na raiz do projeto:

```bash

docker compose -f src/controller/compose.yml up --build

```

Em segundo plano:

```bash

docker compose -f src/controller/compose.yml up --build -d

```

Conferir os serviços:

```bash

docker compose -f src/controller/compose.yml ps

```

Observar API, cron e worker:

```bash

docker compose -f src/controller/compose.yml logs -f api cron worker

```

Encerrar:

```bash

docker compose -f src/controller/compose.yml down

```

### Comandos individuais

API:

```bash

python -m uvicorn src.aplication.main:app --host 0.0.0.0 --port 8000

```

Cron:

```bash

python -m src.aplication.main start_cron

```

Worker:

```bash

celery -A src.infra.manage:celery_app worker --loglevel=INFO

```

Migrações:

```bash

python -m src.infra.manage migration_db

python -m src.infra.manage migration_redis

```

## Testando o fluxo

### Teste ponta a ponta das rotas

Com a stack em execução:

```bash

python -m unittest tests.app -v

```

Esse teste cria, consulta, atualiza e exclui uma instância usando a API real.

### Teste manual imediato do scheduler

Depois de criar uma instância pela API, torne somente esse cron vencido no PostgreSQL:

```sql

UPDATE cron

SET created_at = CURRENT_TIMESTAMP - INTERVAL '2 days'

WHERE instance_id = <ID_DA_INSTANCIA>;

```

Em até aproximadamente dez segundos, os logs devem mostrar:

1. cron lendo o ID;

2. atualização de `created_at`;

3. worker recebendo `execute_task`;

4. requisição externa concluída;

5. resultado salvo em `tasks`;

6. task Celery marcada como concluída.

Confirme o resultado:

```sql

SELECT

t.id,

t.instance\_id,

t.cron\_id,

t.result,

t.created\_at

FROM tasks t

WHERE t.instance_id = <ID_DA_INSTANCIA>

ORDER BY t.created_at DESC;

```

### Inspecionar o schedule

```bash

docker compose -f src/controller/compose.yml exec redis \

redis-cli ZRANGE schedule 0 -1 WITHSCORES

```

## Estrutura do projeto

```text

CronServer/

├── Documents/

│   ├── README.md

│   ├── assets/

│   ├── app/

│   └── layer/

├── src/

│   ├── aplication/

│   ├── controller/

│   ├── domain/

│   ├── infra/

│   ├── logs/

│   ├── repository/

│   └── service/

├── tests/

└── LICENSE

```

## Logs e observabilidade

Os logs seguem este formato:

```text

data | nível | componente | mensagem

```

Exemplo:

```text

2026-09-01 18:18:35,604 | INFO | infra_request | Executando requisição GET

```

As mensagens do console usam cores por área:

| Cor | Área |

| --- | --- |

| Vermelho | Redis |

| Verde | PostgreSQL |

| Azul | Domínio |

| Roxo/magenta | Rotas e Celery |

| Amarelo | Loop de cron |

Somente a mensagem recebe cor; timestamp, nível e componente permanecem no formato padrão. Cada logger também escreve em um arquivo próprio dentro de `src/logs`.

## Documentação complementar

### Aplicação

- [Requisitos do sistema](Documents/app/requisitos.md)

- [Schema do banco](Documents/app/schema.md)

- [Tecnologias](Documents/app/Tecnologias.md)

- [Estrutura visual](Documents/app/Estrutura.pdf)

- [Fluxo visual](Documents/app/Fluxo.pdf)

### Camadas

- [Visão geral das camadas](Documents/layer/README.md)

- [Aplicação](Documents/layer/application.md)

- [Domínio](Documents/layer/domain.md)

- [Infraestrutura](Documents/layer/infrastructure.md)

- [Repositório](Documents/layer/repository.md)

- [Serviço](Documents/layer/service.md)

- [Controller e Docker](Documents/layer/controller.md)

- [Logs](Documents/layer/logs.md)

- [Testes](Documents/layer/tests.md)

## Estado atual e limitações conhecidas

O Cron Server está em fase de MVP. O fluxo principal de criação, agendamento, execução e persistência funciona, mas alguns pontos ainda precisam evoluir:

- a migration Redis usa `fetchone()` e restaura somente um agendamento;

- os padrões de chave usados para ler e gravar cache de requests ainda não são uniformes;

- caches são gravados como hashes, mas o método genérico de leitura atual usa `GET`;

- atualizar `interval` no PostgreSQL não atualiza atualmente o score no schedule;

- a atualização genérica de colunas SQL precisa de comandos seguros por campo;

- o cliente HTTP não possui timeout e espera uma resposta JSON;

- a consulta de tasks entrega somente a execução mais recente;

- o token JWT não possui expiração automática;

- o loop usa polling fixo de dez segundos;

- alguns testes refletem versões anteriores do fluxo e precisam ser realinhados;

- logs em arquivo não possuem rotação.

Esses itens estão documentados por camada para facilitar a evolução sem esconder o comportamento real do código.

## Licença

Copyright © 2026 Brayan.

O projeto utiliza uma licença própria de **uso com atribuição e sem modificações**. Consulte o arquivo [`LICENSE`](LICENSE) antes de usar ou redistribuir o software.

---

<div align="center">

Construído com FastAPI, Celery, Redis, PostgreSQL, Nginx e Docker.

</div>