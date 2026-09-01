from src.logs.log import LogLayer
logger = LogLayer("aplication_cron").config().logger()



"""
Cria o loop  que vai ficar executando as tasks
"""

from src.aplication.tasks.task import execute_task
from src.service.module import client, control_db
from datetime import datetime, timedelta, timezone
import time
class CronError(Exception):
    pass

async def cron_loop() -> None:

    try:

        while True:

            schedule = await client.sorted_get("schedule")

            if schedule is not None:
                

                for instance_id, interval in schedule.items():


                    instance = await control_db.requests.select(search="id", value=instance_id)

                    if instance is None:
                        continue

                    date = datetime.fromisoformat(instance["created_at"])
                    next_run = date + timedelta(days=interval)

                    if datetime.now(timezone.utc) >= next_run:

                        task = execute_task(instance_id=instance_id)
                        task.delay()

            else:

                logger.info("Esperando dados...")
                time.sleep(10)

    except Exception as e:
        logger.error(e)
        raise CronError(e)

                






    


