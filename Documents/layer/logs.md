# Camada de logs

## Objetivo

A camada de logs padroniza mensagens por componente, grava cada logger em arquivo e colore somente a mensagem no console. Isso permite identificar rapidamente a origem de um evento sem colorir timestamp, nível ou nome do logger.

## Estrutura

```text
src/logs/
└── log.py
```

Durante a execução, arquivos `<nome_da_camada>.log` são criados nesse mesmo diretório.

## `LogLayer`

Construção típica:

```python
logger = LogLayer("repository_redis", color="red").config().logger()
```

Parâmetros:

- `layer`: nome usado tanto pelo `logging.getLogger()` quanto pelo arquivo;
- `color`: cor opcional aplicada apenas à mensagem no console.

## Formato

O formato base é:

```text
%(asctime)s | %(levelname)s | %(name)s | %(message)s
```

Exemplo:

```text
2026-09-01 18:21:06,541 | INFO | repository_redis | Adicionando em schedule...
```

No arquivo, a linha permanece sem códigos ANSI. No console, quando existe uma cor, somente `%(message)s` recebe o prefixo e o reset ANSI.

## Cores disponíveis

| Nome | Código ANSI | Associação usada no projeto |
| --- | --- | --- |
| `red` | 31 | Redis. |
| `green` | 32 | Banco de dados/PostgreSQL. |
| `yellow` | 33 | Loop de cron. |
| `blue` | 34 | Domínio/JWT. |
| `magenta` | 35 | Rotas e Celery/tasks. |
| `black` | 30 | Disponível. |
| `cyan` | 36 | Disponível. |
| `white` | 37 | Disponível. |

Uma cor inexistente causa `ValueError` e lista as opções aceitas.

## Handlers

`config()` mantém dois handlers:

### Arquivo

- `logging.FileHandler`;
- encoding UTF-8;
- formato sem cor;
- criado apenas quando não existe outro FileHandler para o mesmo caminho.

### Console

- `logging.StreamHandler`;
- marcado internamente com `_log_layer_console`;
- reutilizado nas próximas configurações do mesmo logger;
- usa formato com ou sem cor.

Essa checagem evita multiplicar a mesma mensagem toda vez que `LogLayer` é configurado novamente no processo.

## Propagação e nível

Cada logger usa nível `INFO` e `propagate = False`. Portanto, a mensagem não sobe para o logger raiz depois de ser processada pelos handlers próprios. Mensagens `DEBUG` não são gravadas com a configuração atual.

## Convenção de nomes

Os nomes atuais seguem área e componente:

```text
infra_connect_db
infra_connect_redis
infra_connect_celery
infra_migration_db
infra_migration_redis
repository_db_requests
repository_db_tasks
repository_redis
aplication_handles_requests
aplication_handles_tasks
aplication_midlleware
aplication_cron
aplication_tasks_execute
domain_jwt
```

## Leitura em Docker

O StreamHandler escreve no fluxo do processo, então Docker Compose agrega as mensagens com o prefixo do serviço:

```text
cron-1   | <mensagem do cron>
worker-1 | <mensagem do Celery ou da aplicação>
api-1    | <mensagem da API>
```

Os códigos de cor podem aparecer literalmente quando a saída é copiada para um ambiente que não interpreta ANSI. Isso não afeta os arquivos de log.

## Responsabilidade de cada origem

- infraestrutura registra criação e teste de conexões, migrações e chamadas HTTP;
- repositório registra consultas, gravações, invalidações e acessos ao Redis;
- aplicação registra entrada de rotas, rate limit, polling e despacho;
- domínio registra criação e leitura de tokens;
- o próprio Celery adiciona logs de recebimento, sucesso e falha das tasks.

## Pontos de atenção

- Não há rotação de arquivos; eles podem crescer enquanto o filesystem do processo existir.
- Os arquivos são gravados dentro de `src/logs`, caminho que pode ser somente leitura em alguns ambientes de produção.
- Tokens completos aparecem em alguns logs do middleware e podem ser informação sensível.
- O loop registra leituras frequentes. O volume depende do intervalo de polling e de onde os logs de leitura estão posicionados.
- Não existe formato JSON estruturado, correlation ID ou integração com observabilidade externa.
