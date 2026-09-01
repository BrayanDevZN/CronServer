from src.logs.log import LogLayer

logger = LogLayer("repository_db_tasks", color="green").config().logger()


"""
Controla a tabela tasks
"""

from sqlalchemy import Engine, text


class TasksDbError(Exception):
    pass


class TasksDb:

    def __init__(self, engine: Engine) -> None:
        self.eng = engine

    # Insere uma execução na tabela tasks
    async def insert(self, instance_id: int, cron_id: int, result: str) -> dict | None:

        try:

            logger.info(f"Salvando resultado da instância {instance_id}...")

            with self.eng.begin() as session:

                task = session.execute(
                    text("""
                        WITH inserted_task AS (
                            INSERT INTO tasks(instance_id, cron_id, result)
                            VALUES(:instance_id, :cron_id, :result)
                            RETURNING *
                        )
                        SELECT r.*, c.*, t.*
                        FROM inserted_task t
                        INNER JOIN requests r ON r.id = t.instance_id
                        INNER JOIN cron c
                            ON c.id = t.cron_id
                            AND c.instance_id = t.instance_id
                    """),
                    {
                        "instance_id": instance_id,
                        "cron_id": cron_id,
                        "result": result,
                    },
                ).mappings().fetchone()

            return task

        except Exception as e:

            logger.error(e)
            raise TasksDbError(e)

    # Busca todo o histórico de execuções de uma requisição
    async def select(self, instance_id: int) -> dict | None:

        try:

            logger.info("Buscando histórico de execuções...")

            with self.eng.begin() as session:

                task = session.execute(
                    text(
                        "select r.*, c.*, t.* from requests r "
                        "inner join cron c on r.id = c.instance_id "
                        "inner join tasks t on r.id = t.instance_id and c.id = t.cron_id "
                        "where t.instance_id = :instance_id "
                        "order by t.created_at desc"
                    ),
                    {"instance_id": instance_id},
                ).mappings().fetchone()

            return task

        except Exception as e:

            logger.error(e)
            raise TasksDbError(e)

    # Atualiza o resultado de uma execução
    async def update(self, instance_id: int, result: str) -> dict | None:

        try:

            logger.info(f"Atualizando tasks da instância {instance_id}...")

            with self.eng.begin() as session:

                task = session.execute(
                    text(
                        "update tasks set result = :result "
                        "where instance_id = :instance_id returning *"
                    ),
                    {"result": result, "instance_id": instance_id},
                ).mappings().fetchone()

            return task

        except Exception as e:

            logger.error(e)
            raise TasksDbError(e)

    # Exclui uma execução do histórico
    async def delete(self, instance_id: int) -> None:

        try:

            logger.info(f"Excluindo tasks da instância {instance_id}...")

            with self.eng.begin() as session:

                session.execute(
                    text("delete from tasks where instance_id = :instance_id"),
                    {"instance_id": instance_id},
                )

        except Exception as e:

            logger.error(e)
            raise TasksDbError(e)
