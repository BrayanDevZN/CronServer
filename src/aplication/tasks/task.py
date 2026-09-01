"""
Trasforma execute em task
"""

from src.infra.manage import celery_app
from src.aplication.tasks.execute import ExecuteTask
import asyncio
@celery_app.task(name="execute_task")
def execute_task(instance:dict):

    task = ExecuteTask(instance=instance)

    asyncio.run(task.run())
