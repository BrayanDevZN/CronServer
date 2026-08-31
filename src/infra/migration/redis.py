from src.logs.log import LogLayer
logger = LogLayer("infra_migration_redis").config().logger()


"""
Puxa os dados do banco de dados e manda pro redis
"""

from sqlalchemy import text, Engine
from redis import Redis

class MirgationRedisError(Exception):
    pass


class MigrationRedis:

    def __init__(self, engine: Engine, redis_connection:Redis)-> None:

        self.eng = engine
        self.redis = redis_connection


    #Cria a query que vai puxar os dados do banco
    def _query(self) -> None:

        try:

            logger.info("Lendo dados do banco de dados...")


            with self.eng.begin() as session:

                result = session.execute(
                    text(
                        """
                            select r.id, c.interval, c.created_at from requests r inner join cron c on r.id = c.instance_id
                        """

                    )
                )

            self.result = result.mappings().fetchone()
           
        except Exception as e:

            logger.error(e)
            raise MirgationRedisError(e)

    #Confere se existe dados 
    def _exists(self) -> None:

        if not self.result:

            logger.info("Ainda não ha dados salvos!!")
            self.exists = False

        else:
            self.exists = True


    #Salva result no redis
    def _save(self) -> None:

        logger.info("Salvando dados do banco no redis...")

        with self.redis.pipeline(transaction=True) as session:

            session.multi()
            session.zadd(
                name="schedule",
                mapping=self.result
            )

            session.execute()


    #Executa todos os metodos, e so executa _save se result não for False
    def run(self) -> None:

        self._query()
        self._exists()
        if not self.exists:
            return

        self._save()



        
        
