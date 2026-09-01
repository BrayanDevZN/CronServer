# Camada de testes

## Objetivo

A pasta `tests` verifica componentes isolados, integrações com PostgreSQL e Redis, rotas HTTP, worker Celery, loop de cron e o fluxo completo da aplicação. Ela mistura testes unitários, de integração e ponta a ponta; por isso, cada arquivo tem requisitos diferentes para execução.

## Estrutura

```text
tests/
├── app.py
├── auth.py
├── connect.py
├── cron.py
├── db.py
├── log.py
├── migration.py
├── redis.py
├── request.py
├── requests_router.py
├── task.py
└── tasks_router.py
```

## Categorias

| Categoria | Arquivos | Recursos necessários |
| --- | --- | --- |
| Unitário/mocks | `cron.py`, `request.py` | Ambiente importável; algumas importações ainda inicializam serviços. |
| Domínio | `auth.py` | Segredo e importação do serviço. |
| Infraestrutura manual | `connect.py`, `log.py`, `migration.py` | PostgreSQL, Redis e ambiente. |
| Repositório | `db.py`, `redis.py` | PostgreSQL e Redis reais. |
| Rotas | `requests_router.py`, `tasks_router.py` | API em execução, PostgreSQL e Redis. |
| Worker | `task.py` | Celery worker, broker, PostgreSQL e Redis. |
| Ponta a ponta | `app.py` | Stack completa e acesso à URL externa. |

## Teste ponta a ponta

### `app.py`

Executa o ciclo público inteiro contra `CRON_SERVER_URL`, cujo padrão é `http://127.0.0.1:8000`:

1. cria uma URL única no httpbin;
2. confirma o token retornado;
3. consulta o agendamento;
4. atualiza o intervalo;
5. consulta tasks;
6. exclui o agendamento;
7. confirma que a consulta posterior retorna `401`.

O `tearDown()` tenta excluir o registro se o teste falhar depois da criação, reduzindo resíduos. O timeout pode ser configurado por `CRON_SERVER_TIMEOUT`.

Execução:

```bash
python -m unittest tests.app -v
```

Esse teste verifica as rotas, mas não espera um dia para validar a execução agendada. Para testar scheduler e worker imediatamente, é necessário tornar o `cron.created_at` vencido em um registro controlado.

## Autenticação

### `auth.py`

Valida dois cenários:

- um payload codificado por `jwt_auth.create()` é recuperado por `read()`;
- um token inválido levanta `JwtAuthError`.

Como o teste usa a instância de serviço, a importação pode iniciar conexões da infraestrutura mesmo que o comportamento testado seja apenas JWT.

## Conexões

### `connect.py`

É um teste manual executável. Carrega o ambiente, cria conexões independentes e valida:

- PostgreSQL com `SELECT 1`;
- Redis com `PING`.

Fecha a engine e o Redis no final. Se qualquer conexão falhar, termina com código diferente de zero.

```bash
python -m tests.connect
```

## Loop do cron

### `cron.py`

Usa `IsolatedAsyncioTestCase`, `AsyncMock` e patch para controlar uma iteração do loop sem aguardar indefinidamente. Os cenários são:

- schedule vencido deve disparar a task;
- schedule ainda dentro do intervalo não deve disparar;
- ID que não existe no repositório deve ser ignorado.

O teste interrompe o loop fornecendo `asyncio.CancelledError` na leitura seguinte. Esse arquivo é a principal proteção da regra `created_at + interval`.

## Repositórios

### `db.py`

Prepara registros reais no banco e testa:

- insert, select, update e delete de requests;
- insert, select, update e delete de tasks.

O setup guarda IDs próprios e o teardown remove dados e caches criados. Por acessar a configuração compartilhada, é um teste de integração e não deve apontar para uma base com dados importantes sem isolamento.

### `redis.py`

Cria nomes únicos com UUID e verifica:

- contador com `incr` e leitura;
- criação de hash;
- sorted set e ordenação por score;
- exclusão de chave inteira;
- exclusão de apenas um membro com `ZREM`.

O teardown apaga todas as chaves exclusivas do teste.

## Executor HTTP

### `request.py`

Substitui `requests.request` por mock para validar método, URL, headers e JSON enviados, além da rejeição de método inválido. Isso evita chamadas externas durante o teste unitário.

Existe uma divergência atual: `HttpRequest.run()` devolve `response.json()`, enquanto o teste configura um mock de resposta e espera o próprio objeto `response`. O teste também precisa importar `HttpRequestError` para validar o cenário inválido. Esses pontos devem ser alinhados antes de considerar essa suíte estável.

## Rotas de requests

### `requests_router.py`

Executa chamadas reais à API:

- `POST /requests/`;
- `GET /requests/{token}`;
- `PATCH /requests/`;
- `DELETE /requests/`.

Alguns cenários criam a instância diretamente no PostgreSQL e geram um token com o serviço de domínio. O teardown remove caches e registros usando os `public_id` conhecidos.

## Rota de tasks

### `tasks_router.py`

Cria request, cron e task diretamente no banco, gera um token e chama `GET /tasks/`. Confirma que o conteúdo é um dicionário e que o resultado é `success`.

## Worker Celery

### `task.py`

Sobe um pequeno servidor HTTP local em uma porta aleatória, cria request e cron no PostgreSQL e envia `execute_task.delay(instance)` ao worker real. Depois confere o estado Celery e a task gravada.

A URL `127.0.0.1` pertence ao processo que executa o teste. Se o worker estiver dentro de outro contêiner, o `127.0.0.1` do worker não aponta para o host do teste; nesse cenário, a rede do teste precisa ser adaptada.

O teste atual se chama `test_worker_updates_cron_and_saves_result` e espera que o worker altere `cron.created_at`. Na implementação atual, essa atualização foi movida para o loop antes do `delay()`, enquanto `ExecuteTask` somente executa e salva. Portanto, essa expectativa está desatualizada para o desenho atual.

## Migrações e logs

### `migration.py`

Executa os comandos `migration_db` e `migration_redis` em subprocessos. Esse arquivo altera estado real e não é um teste somente de leitura.

```bash
python -m tests.migration
```

Em Docker, as migrações já são representadas por serviços próprios e não precisam ser disparadas por esse script durante o startup normal.

### `log.py`

Cria um logger de teste e emite uma mensagem. É uma verificação manual simples do handler de arquivo e console.

## Execução sugerida

Com a stack em execução, arquivos individuais podem ser chamados com unittest:

```bash
python -m unittest tests.auth -v
python -m unittest tests.cron -v
python -m unittest tests.redis -v
python -m unittest tests.db -v
python -m unittest tests.requests_router -v
python -m unittest tests.tasks_router -v
python -m unittest tests.app -v
```

Os testes que usam recursos externos devem ser executados de maneira controlada, porque podem escrever no banco configurado no `.env`.

## Dados de teste e limpeza

Boas práticas já presentes:

- UUIDs evitam colisões de URL e chave;
- teardown remove registros conhecidos;
- foreign keys em cascata simplificam a limpeza;
- mocks isolam a biblioteca Requests em teste unitário;
- o loop é interrompido artificialmente nos testes.

Riscos atuais:

- algumas suítes usam a base configurada da aplicação, inclusive se ela for externa;
- `migration.py` cria estrutura e reconstrói schedule;
- falhas abruptas antes do teardown podem deixar registros;
- caches possuem vários padrões de chave, dificultando garantir limpeza total;
- a suíte não está completamente alinhada às mudanças mais recentes do cron e do executor.

## Critério de teste completo do scheduler

Um teste operacional completo deve confirmar esta sequência:

1. criar request e cron pela API;
2. confirmar o member no sorted set `schedule`;
3. ajustar somente o registro de teste para uma data vencida;
4. observar o cron atualizar `created_at`;
5. observar o worker receber exatamente uma task;
6. confirmar o resultado em `tasks`;
7. aguardar outra iteração e confirmar que não houve duplicação;
8. excluir a instância e confirmar a remoção do banco e do sorted set.
