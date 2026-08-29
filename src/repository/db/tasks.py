from src.logs.log import LogLayer

logger = LogLayer("repository_db_tasks").config().logger()


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
    async def insert(self, instance_id: int, cron_id: int, result: str) -> dict:

        try:

            logger.info(f"Salvando resultado da instância {instance_id}...")

            with self.eng.begin() as session:

                task = session.execute(
                    text(
                        "insert into tasks(instance_id, cron_id, result) "
                        "values(:instance_id, :cron_id, :result) returning *"
                    ),
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
    async def select(self, public_id: int | str) -> list[dict]:

        try:

            logger.info("Buscando histórico de execuções...")

            with self.eng.begin() as session:

                tasks = session.execute(
                    text(
                        "select r.*, c.*, t.* from requests r "
                        "inner join cron c on r.id = c.instance_id "
                        "inner join tasks t on r.id = t.instance_id and c.id = t.cron_id "
                        "where r.public_id = :public_id "
                        "order by t.created_at desc"
                    ),
                    {"public_id": public_id},
                ).mappings().fetchall()

            return tasks

        except Exception as e:

            logger.error(e)
            raise TasksDbError(e)

    # Atualiza o resultado de uma execução
    async def update(self, task_id: int, result: str) -> dict | None:

        try:

            logger.info(f"Atualizando task {task_id}...")

            with self.eng.begin() as session:

                task = session.execute(
                    text(
                        "update tasks set result = :result "
                        "where id = :task_id returning *"
                    ),
                    {"result": result, "task_id": task_id},
                ).mappings().fetchone()

            return task

        except Exception as e:

            logger.error(e)
            raise TasksDbError(e)

    # Exclui uma execução do histórico
    async def delete(self, task_id: int) -> None:

        try:

            logger.info(f"Excluindo task {task_id}...")

            with self.eng.begin() as session:

                session.execute(
                    text("delete from tasks where id = :task_id"),
                    {"task_id": task_id},
                )

        except Exception as e:

            logger.error(e)
            raise TasksDbError(e)
