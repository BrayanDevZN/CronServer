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

    async def select(self, value:int|str, search:Literal["public_id", "url", "id"]) -> dict|None:

        try:

            logger.info("Buscando url...")

            columns = (
                "select r.id, r.public_id, r.url, r.headers, r.body, "
                "r.method, c.id as cron_id, c.interval, c.created_at "
                "from requests r "
                "inner join cron c on r.id = c.instance_id "
            )

            if search == "public_id":
                sql = columns + "where r.public_id = :value"

            elif search == "url":

                sql = columns + "where r.url = :value"

            else:

                sql = columns + "where r.id = :value"



        
                   

            with self.eng.begin() as session:

                result = session.execute(
                    text(sql),
                    {"value": value}
                    )


            return result.mappings().fetchone()

        except Exception as e:

            logger.error(e)
            raise RequestsDbError(e)


    async def update(self, public_id:str|int, set:Literal["method", "headers", "body", "interval", "created_at"], value:Any) -> dict:


        try:

            logger.info(f"Atualizando {set}...")

            with self.eng.begin() as session:


                if set == "interval":

                    result = session.execute(
                        text("update cron set interval = :value " \
                        "where instance_id = (select id from requests where public_id = :public_id)" \
                        "returning *"), {"value": value,"public_id": public_id}
                    )

                elif set == "created_at":
                    result = session.execute(
                                            text("update cron set created_at = :value " \
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

                


        

        
