# Camada de domínio

## Objetivo

A camada de domínio reúne as regras e os formatos que identificam o negócio sem conhecer PostgreSQL, Redis, Docker ou detalhes das rotas. No estado atual do projeto, ela possui duas responsabilidades principais:

- validar a estrutura das operações de requests;
- criar e validar tokens JWT que identificam uma instância.

## Estrutura

```text
src/domain/
├── module.py
├── auth/
│   └── jwt.py
└── schema/
    └── requests.py
```

## Schemas de requests

Os schemas usam Pydantic e são aplicados automaticamente pelo FastAPI.

### `RequestsModelCreate`

Representa a entrada de criação:

| Campo | Tipo | Regra atual |
| --- | --- | --- |
| `url` | `str` | Obrigatório. Não há validação específica de URL no schema. |
| `method` | `Literal` | Aceita somente `POST`, `GET`, `PATCH`, `PUT` ou `DELETE`, em maiúsculas. |
| `body` | `dict \| str` | Obrigatório; aceita objeto ou texto. |
| `headers` | `dict \| str` | Obrigatório; aceita objeto ou texto. |
| `interval` | `int` | Obrigatório; o loop interpreta o valor em dias. |

Exemplo válido:

```json
{
  "url": "https://example.com/process",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer value"
  },
  "body": {
    "action": "sync"
  },
  "interval": 1
}
```

### `RequestsModelUpdate`

Representa uma atualização parcial:

| Campo | Tipo | Regra atual |
| --- | --- | --- |
| `set` | `Literal` | `method`, `headers`, `body` ou `interval`. |
| `value` | `str` | Todo valor chega ao handler como texto. |

O schema impede a atualização pública de `created_at`, `url`, IDs e outros campos. O loop, no entanto, pode atualizar `created_at` diretamente ao chamar o repositório.

## Autenticação JWT

### `JwtAuth`

`domain/auth/jwt.py` implementa a criação e a leitura dos tokens.

Configuração:

- algoritmo: `HS256`;
- chave: recebida no construtor como `sing`;
- biblioteca: PyJWT.

### Criação

`create(payload)` codifica qualquer dicionário fornecido. Na criação de um agendamento, o payload atual é:

```json
{
  "public_id": "9b722079-9aa9-4447-a944-6b223bdc9f4f",
  "created_at": "2026-09-01 18:21:05.852082+00:00"
}
```

O token não contém atualmente `exp`, `iat`, emissor ou audiência. Logo, não expira automaticamente; ele permanece válido enquanto a assinatura for aceita e o `public_id` ainda existir no banco.

### Leitura

`read(token)` valida a assinatura com a mesma chave e o algoritmo `HS256`, retornando o payload. Falhas são registradas no log e encapsuladas em `JwtAuthError`.

## Identidade no domínio

O sistema possui três identificadores relacionados:

- `id`: identificador interno numérico da request;
- `public_id`: UUID que pode sair do banco e compõe o token;
- token JWT: credencial apresentada nas rotas protegidas.

O token não substitui a consulta de existência. A dependência da aplicação lê o `public_id` do token e confirma no repositório que a instância continua cadastrada. Depois da exclusão, um token corretamente assinado deixa de autorizar operações porque não existe mais registro correspondente.

## Módulo de exportação

`domain/module.py` oferece um ponto curto de importação:

```python
from src.domain.auth.jwt import JwtAuth
import src.domain.schema.requests as RequestsModel
```

A camada de serviço usa esse módulo para construir `jwt_auth` e expor `RequestsModel` à aplicação.

## Dependências permitidas

A camada depende apenas de bibliotecas de domínio/validação:

- PyJWT;
- Pydantic;
- módulo de logs do projeto.

Ela não deve depender de FastAPI, SQLAlchemy, Redis ou Celery para preservar a separação das regras.

## Erros

`JwtAuthError` representa qualquer falha ao codificar ou decodificar tokens. Os schemas geram os erros de validação padrão do Pydantic quando o corpo não corresponde aos tipos ou literals definidos.

## Pontos de atenção da implementação atual

- `sing` aparenta representar `sign` ou segredo de assinatura; o nome é mantido porque também é a variável de ambiente usada.
- Não há validação de URL com `HttpUrl`.
- Não há restrição de intervalo mínimo; zero e números negativos passam pelo schema.
- Headers e body aceitam texto, mas a camada de controle executa `json.dumps()` incondicionalmente na criação.
- O JWT não expira automaticamente.
- O domínio ainda não modela entidades próprias para request, cron ou task; os dados circulam principalmente como dicionários.
