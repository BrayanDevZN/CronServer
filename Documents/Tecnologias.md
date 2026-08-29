# Tecnologias do Projeto

Stack planejada para o desenvolvimento do **Cron Server**, responsável por cadastrar, agendar e executar requisições HTTP.

## Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)
![Requests](https://img.shields.io/badge/Requests-HTTP-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

## Responsabilidades

| Tecnologia | Responsabilidade no projeto |
| --- | --- |
| **Python** | Linguagem principal da aplicação. |
| **FastAPI** | Construção da API HTTP para criação e consulta das tarefas. |
| **Celery** | Processamento assíncrono e execução das tarefas agendadas. |
| **Requests** | Envio das requisições HTTP cadastradas pelos usuários. |
| **Redis** | Intermediação das mensagens entre a API e os workers do Celery. |
| **PostgreSQL** | Persistência das tarefas, configurações e resultados das execuções. |
| **Docker** | Padronização e isolamento dos serviços da aplicação. |

## Fluxo entre as tecnologias

```text
Usuário
   │
   ▼
FastAPI ─────► PostgreSQL
   │          tarefas e resultados
   ▼
 Redis
   │
   ▼
Celery Worker ─────► Requests ─────► URL de destino
```

## Organização dos serviços

- **API:** recebe, valida e registra as tarefas.
- **Worker:** executa as requisições em segundo plano.
- **Broker:** distribui as tarefas pendentes aos workers.
- **Banco de dados:** mantém as configurações e o histórico de execução.
- **Contêineres:** facilitam a execução conjunta e consistente dos serviços.

> As versões das tecnologias serão definidas durante a configuração inicial do projeto.
