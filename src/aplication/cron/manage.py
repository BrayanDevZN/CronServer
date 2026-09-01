from src.logs.log import LogLayer
logger = LogLayer("aplication_cron", color="yellow").config().logger()



"""
Cria o loop  que vai ficar executando as tasks
"""

from src.aplication.tasks.task import execute_task
from src.service.module import client, control_db
from datetime import datetime, timedelta, timezone 
import asyncio
class CronError(Exception):
    pass

async def cron_loop() -> None:

    try:

        
        read_log = True

        while True:

            if read_log:
                
                logger.info("Esperando dados de schedule...")

            schedule = await client.sorted_get("schedule")
            

            if schedule:
                

                for instance_id, interval in schedule:


                    instance = await control_db.requests.select(search="id", value=instance_id)

                    if instance is None:
                        continue

                    date = datetime.fromisoformat(instance["created_at"])
                    next_run = date + timedelta(days=interval)
                    now = datetime.now(timezone.utc)

                    if now>= next_run:

                        await control_db.requests.update(public_id=instance["public_id"], set="created_at", value=now)

                        execute_task.delay(instance)

                    read_log = True

            else:
                read_log = False


                await asyncio.sleep(10)

    except Exception as e:
        logger.error(e)
        raise CronError(e)

                






    
