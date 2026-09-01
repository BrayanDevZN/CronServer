from src.logs.log import LogLayer
logger = LogLayer("infra_connect_redis", color="red").config().logger()



"""
Cria conexão com redis
"""
import redis

class RedisConnect:

    def __init__(self, port:str, host:str)-> None:

        self.port = port
        self.host = host


    #Cria a conexão
    def _connect(self) -> None:

        
            logger.info("Criando conexão com redis...")

            self.con = redis.Redis(
                port=self.port, host=self.host, decode_responses=True
            )

       

    #testa a conexão 
    def _test(self) -> None:

        try:

             logger.info("Testando conexão com redis...")

             self.con.ping()

        except redis.ConnectionError as e:

             logger.error(e)
             raise redis.ConnectionError(e)

    #Executa os metodos e retorna conexão
    def run(self) -> redis.Redis:

         self._connect()
         self._test()

         return self.con






        

