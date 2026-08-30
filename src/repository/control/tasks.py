"""
Junta a classe que controla tasks com cache
"""

from sqlalchemy import Engine
from redis import Redis

from src.repository.db.tasks import TasksDb
from src.repository.redis.control import RedisControl
import json


class TasksControl:

    def __init__(self, engine:Engine, redis_connection:Redis)-> None:

        self.db = TasksDb(engine)
        self.client = RedisControl(redis_connection)


    #Insere na tabela e cria cache
    async def insert(self, instance_id: int, cron_id: int, result: str) -> dict:

        result = await self.db.insert(instance_id=instance_id, cron_id=cron_id, result=result)
        result = dict(result)
        result["created_at"] = str(result["created_at"])
        result["headers"] = json.dumps(result["headers"])
        result["body"] = json.dumps(result["body"])
        result["public_id"] = str(result["public_id"])

        await self.client.hash(name=f"task:instance_id:{result["instance_id"]}", data=result)

        return result

    #Le em tasks e salva cache
    async def select(self, instance_id: int) -> dict:

        cache = await self.client.get(name=f"task:instance_id:{instance_id}")

        if cache is not None:

            return cache

        result = await self.db.select(instance_id=instance_id)


        if result is None:
            return result

        result = dict(result)
        result["created_at"] = str(result["created_at"])
        result["headers"] = json.dumps(result["headers"])
        result["body"] = json.dumps(result["body"])
        result["public_id"] = str(result["public_id"])

        await self.client.hash(name=f"task:instance_id:{instance_id}", data=result)

        return result

    #Atualiza tasks e invalida cache
    async def update(self, instance_id: int, result: str) -> dict:

        result = await self.db.update(instance_id=instance_id, result=result)
        result = dict(result)

        await self.client.delete(name=f"task:instance_id:{instance_id}")

        return result

    #Deleta uma task e invalida cache
    async def delete(self, instance_id:int) -> None:

        await self.db.delete(instance_id=instance_id)
        await self.client.delete(name=f"task:instance_id:{instance_id}")
