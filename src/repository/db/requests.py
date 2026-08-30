from src.logs.log import LogLayer
logger = LogLayer("repository_db_requests").config().logger()


"""
Controla a tabela requests
"""

from sqlalchemy import Engine, text
from typing import Literal, Any


class RequestsDbError(Exception):
    pass


class RequestsDb:

    def __init__(self, engine: Engine)-> None:
        self.eng = engine


    #Insere na tabela requests e interval
    async def insert(self, url:str, 
               method:Literal["POST", "GET", "PATCH", "PUT", "DELETE"], 
               body:dict, headers:dict, interval:int) -> dict:


        try:

            logger.info(f"salvando {url} com metodo {method} e com intervalo de execução de {interval}...")


            with self.eng.begin() as session:

                result = session.execute(
                    text("insert into requests(url, method, headers, body) " \
                    "values(:url, :method, :headers, :body) returning *"),
                    {"url": url, "method": method, "headers": headers, "body":body}
                ).mappings().fetchone()


                result_cron = session.execute(
                    text("insert into cron(instance_id, interval) values(:instance_id, :interval) returning *"),
                    {"instance_id": result["id"], "interval": interval}
                ).mappings().fetchone()

                result = dict(result) | dict(result_cron)

                
            return result

        except Exception as e:

            logger.error(e)
            raise RequestsDbError(e)

    async def select(self, public_id:int|str) -> dict|None:

        try:

            logger.info("Buscando url...")

            with self.eng.begin() as session:

                result = session.execute(
                    text("select r.*, c.* from requests r inner join cron c on r.id = c.instance_id where r.public_id = :public_id"),
                    {"public_id": public_id}
                    )


            return result.mappings().fetchone()

        except Exception as e:

            logger.error(e)
            raise RequestsDbError(e)


    async def update(self, public_id:str|int, set:Literal["method", "headers", "body", "interval"], value:Any) -> dict:


        try:

            logger.info(f"Atualizando {set}...")

            with self.eng.begin() as session:


                if set == "interval":

                    result = session.execute(
                        text("update cron set interval = :value " \
                        "where instance_id = (select id from requests where public_id = :public_id)" \
                        "returning *"), {"value": value,"public_id": public_id}
                    )

                else:

                    result = session.execute(
                        text("update requests set :set = :value where public_id = :public_id returning *"),
                        {"set":set, "value": value, "public_id":public_id}
                    )

            return result.mappings().fetchone()

        except Exception as e:

            logger.error(e)

            raise RequestsDbError(e)

    async def delete(self, public_id:int|str) -> None:

        try:

            logger.info("Deletando dados...")

            with self.eng.begin() as session:

                session.execute(
                    text("delete from requests where public_id = :public_id"), {"public_id":public_id}
                )


        except Exception as e:

            logger.error(e)

            raise RequestsDbError(e)

                


        

        
