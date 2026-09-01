# Cron Server — Requisitos do Sistema

## Visão geral

O **Cron Server** será responsável por agendar e executar requisições HTTP em intervalos definidos pelo usuário.

O usuário deverá informar os dados da requisição e o intervalo de execução. O servidor armazenará essas informações, criará uma tarefa agendada e retornará um token para que o usuário possa acompanhar sua execução.

## Fluxo principal

1. O usuário envia os dados da requisição HTTP e o intervalo desejado.
2. O servidor valida e armazena os dados recebidos.
3. O servidor cria uma nova tarefa agendada.
4. Um token único é retornado ao usuário.
5. Ao atingir o intervalo definido, o servidor executa a requisição HTTP.
6. O resultado da execução é armazenado.
7. O usuário consulta a tarefa utilizando o token recebido.

## Dados de entrada

Para criar uma tarefa, o usuário deverá informar:

| Campo | Descrição |
| --- | --- |
| `url` | Endereço para o qual a requisição será enviada. |
| `method` | Método HTTP da requisição, como `GET`, `POST`, `PUT`, `PATCH` ou `DELETE`. |
| `headers` | Cabeçalhos HTTP que serão enviados. |
| `body` | Corpo da requisição, quando aplicável. |
| `interval` | Intervalo de tempo entre as execuções. |

## Requisitos funcionais

### RF01 — Criar uma tarefa

O sistema deve permitir a criação de uma tarefa agendada a partir dos dados enviados pelo usuário.

### RF02 — Armazenar a configuração

O sistema deve armazenar a URL, o método HTTP, os cabeçalhos, o corpo da requisição e o intervalo de execução.

### RF03 — Gerar um token

Ao criar uma tarefa, o sistema deve gerar e retornar um token único para sua identificação e consulta.

### RF04 — Executar a requisição

O sistema deve enviar a requisição HTTP para a URL configurada sempre que o intervalo definido for atingido.

### RF05 — Armazenar o resultado

O sistema deve armazenar o resultado de cada execução da tarefa.

### RF06 — Consultar o status

O sistema deve permitir que o usuário consulte o status da tarefa utilizando o token recebido na criação.

## Informações da execução

Sempre que uma requisição for executada, o sistema deverá registrar, no mínimo:

- data e hora da execução;
- status da execução;
- código de status HTTP retornado;
- resposta recebida ou mensagem de erro.

## Status sugeridos

| Status | Descrição |
| --- | --- |
| `scheduled` | A tarefa foi criada e aguarda a próxima execução. |
| `running` | A requisição está sendo executada. |
| `success` | A última execução foi concluída com sucesso. |
| `failed` | A última execução terminou com erro. |
