"""
Junta a classe que controla requests com cache
"""

from sqlalchemy import Engine
from redis import Redis

from src.repository.db.requests import RequestsDb
from src.repository.redis.control import RedisControl
from typing import Literal, Any
import json 
class RequestsControl:

    def __init__(self, engine:Engine, redis_connection:Redis)-> None:

        self.client = RedisControl(connection=redis_connection)
        self.db = RequestsDb(engine=engine)


    #Insere e salva cache
    async def insert(self, url:str, 
               method:Literal["POST", "GET", "PATCH", "PUT", "DELETE"], 
               body:dict, headers:dict, interval:int) -> dict:

        headers, body = json.dumps(headers), json.dumps(body)

       

        result = await self.db.insert(url=url, method=method, body=body, headers=headers, interval=interval)
        result["headers"] = json.dumps(result["headers"])
        result["body"] = json.dumps(result["body"])

        result = dict(result)
        result["public_id"] = str(result["public_id"])
        result["created_at"] = str(result["created_at"])

        
        await self.client.hash(name=f"request:{result["public_id"]}", data=result)
       
        return result


    #Confere se existe no cache, se exitir, retorna ele, se não, le do banco, e se o cache for none, ele salva
    async def select(self, value:int|str, search:Literal["public_id", "url"]) -> dict|None:

        cache = await self.client.get(f"request:{search}")

        if cache is not None:

            return cache

        result = await self.db.select(search=search, value=value)

        if result is None:

            return result

        result = dict(result)

        result["public_id"] = str(result["public_id"])
        result["created_at"] = str(result["created_at"])
        result["headers"] = json.dumps(result["headers"])
        result["body"] = json.dumps(result["body"])

        await self.client.hash(name=f"request:{public_id}", data=result)

        return result

    #Atualiza os dados e invalida cache
    async def update(self, public_id:str|int, set:Literal["method", "headers", "body", "interval"], value:Any) -> dict:

        result = await self.db.update(public_id=public_id, set=set, value=value)

        await self.client.delete(name=f"request:{public_id}")

        result = dict(result)
        return result


    #Deleta os dados e invalida cache
    async def delete(self, public_id:str|int) -> None:

        await self.db.delete(public_id=str(public_id))
        await self.client.delete(name=f"request:{public_id}")

        



        