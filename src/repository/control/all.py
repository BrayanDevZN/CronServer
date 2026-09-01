"""
Junta a classe que busca todos os dados com cache 
"""

from redis import Redis
from sqlalchemy import Engine
from src.repository.db.all import AllDb
from src.repository.redis.control import RedisControl


class AllDbControl:

    def __init__(self, engine:Engine, redis_connection:Redis)-> None:

        self.db = AllDb(engine=engine)
        self.client = RedisControl(redis_connection)


    #Faz a query e salva cache
    async def get(self) -> None|dict:

        cache = self.client.get("all_instances")

        if cache is not None:

            return cache

        result = self.db.get()

        if result is None:

            return result

        await self.client.hash(data=result, name="all_instances")




        return result



        
