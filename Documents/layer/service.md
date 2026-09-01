# Camada de serviço

## Objetivo

A camada de serviço é o ponto de composição entre domínio, infraestrutura e repositório. Ela cria as instâncias compartilhadas que a aplicação usa, evitando que cada rota, task ou loop refaça a montagem das dependências.

## Estrutura

```text
src/service/
├── auth.py
├── db.py
└── module.py
```

## Serviço de autenticação

### `auth.py`

Importa `envroins` da infraestrutura, obtém `sing` e constrói:

```python
jwt_auth = JwtAuth(sing=envroins["sing"])
```

Também importa `RequestsModel`, permitindo que o módulo agregador o exponha junto com `jwt_auth`.

O objeto é singleton por processo Python: API, cron e worker possuem suas próprias instâncias em memória, todas configuradas com o mesmo segredo de ambiente.

## Serviço de dados

### `db.py`

Importa a conexão Redis e a engine PostgreSQL já criadas por `infra.manage`. Em seguida constrói:

```python
control_db = ControlDb(engine=engine, redis_connection=client)
client = RedisControl(connection=client)
```

Os nomes representam duas interfaces diferentes:

- `control_db`: fachada de alto nível para requests, tasks e consultas agregadas;
- `client`: controle de baixo nível para chaves, hashes e sorted sets do Redis.

O cliente Redis bruto existe dentro dos controles como atributo interno, mas a aplicação normalmente usa essas duas abstrações.

## Módulo agregador

### `module.py`

Reexporta os objetos mais usados:

| Nome | Origem | Consumidores |
| --- | --- | --- |
| `client` | `service.db` | Middleware e loop de cron. |
| `control_db` | `service.db` | Rotas, dependência, loop e worker. |
| `HttpRequest` | `infra.manage` | Executor da task. |
| `jwt_auth` | `service.auth` | Rotas e dependência. |
| `RequestsModel` | `service.auth`/domínio | Handlers FastAPI. |

Assim, componentes da aplicação podem usar uma importação única:

```python
from src.service.module import control_db, client, jwt_auth
```

## Ordem de construção

Ao importar `src.service.module`, ocorre esta sequência:

```text
service.module
├── service.db
│   ├── infra.manage
│   │   ├── lê ambiente
│   │   ├── conecta PostgreSQL
│   │   ├── conecta Redis
│   │   └── cria Celery
│   ├── cria ControlDb
│   └── cria RedisControl
└── service.auth
    ├── reutiliza ambiente
    └── cria JwtAuth
```

Isso caracteriza uma composição antecipada: as dependências ficam prontas na importação, e uma falha de conexão impede o processo de subir.

## Limites da camada

A camada não deve conter SQL, regras de schedule nem código de rotas. Seu papel é ligar implementações concretas e fornecer uma API de dependências simples para a aplicação.

## Ciclo de vida

As conexões são mantidas durante toda a vida do processo. Não existe hoje um hook explícito de startup/shutdown do FastAPI para criar ou fechar engine e Redis. O encerramento depende da finalização do processo e dos mecanismos das bibliotecas.

## Pontos de atenção

- Importar `service.module` tem efeitos colaterais de rede.
- Testes que importam o serviço precisam de todas as variáveis e conexões reais, salvo quando os objetos são substituídos por mocks.
- A mesma palavra `client` muda de cliente Redis bruto para `RedisControl` dentro de `service/db.py`; isso funciona, mas exige atenção durante manutenção.
- Não há injeção de dependência por request; os objetos são globais por processo.
- API, cron e worker não compartilham memória. Eles compartilham estado somente por PostgreSQL, Redis e Celery.
