from src.logs.log import LogLayer
logger = LogLayer("repository_db_all", color="green").config().logger()




"""
Retorna os dados de todas as instancias
"""

from sqlalchemy import Engine, text
class AllDbError(Exception):
    pass

class AllDb:

    def __init__(self, engine:Engine)-> None:

        self.eng = engine


    #Executa a query que pega os dados das requisições
    async def get(self) -> None|dict:


        try:

            logger.info("Buscando dados de todas as instancias...")


            with self.eng.begin() as session:

                result = session.execute(
                    text("select r.id, c.created_at inner join cron c on c.instance_id = r.id")
                )

            return dict(result.mappings().fetchall())


        except Exception as e:

            logger.error(e)
            raise AllDbError(e)

            


        
