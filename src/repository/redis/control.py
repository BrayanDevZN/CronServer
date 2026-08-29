from src.logs.log import LogLayer
logger = LogLayer("repository_redis").config().logger()


"""
Controla redis
"""

from redis import Redis, WatchError


class RedisControlError(Exception):
    pass


class RedisControl:

    def __init__(self, connection:Redis)-> None:

        self.client =connection


    #Cria uma operação atomica que incrementa um numero a mais automatico
    async def incr(self, name:str, time:str|None = None) -> None:

        while True:

            try:
                logger.info(f"Adicionando em {name}...")

                with self.client.pipeline(transaction=True) as client:

                    client.watch(name)

                    client.multi()

                    client.incr(name)
                    client.expire(time=60 if time is None else time, name=name)

                    client.execute()

                    break

            except WatchError:

                logger.warning(f"Alguem ja estava alterando {name}, então a operação vai tentar ser executada novamente!!")
                continue

    #Salva um hash no redis
    async def hash(self, name:str, data:dict, time:str|None = None) -> None:

        while True:
        
                    try:
                        logger.info(f"Adicionando em {name}...")
        
                        with self.client.pipeline(transaction=True) as client:
        
                            client.watch(name)
        
                            client.multi()
        
                            client.hset(name=name, mapping=data)
                            client.expire(time=60 if time is None else time, name=name)
        
                            client.execute()
        
                            break
        
                    except WatchError:
        
                        logger.warning(f"Alguem ja estava alterando {name}, então a operação vai tentar ser executada novamente!!")
                        continue


    #salva em formato de sorted set
    async def sorted_set(self, name:str, data:dict) -> None:

         while True:
                 
                             try:
                                 logger.info(f"Adicionando em {name}...")
                 
                                 with self.client.pipeline(transaction=True) as client:
                 
                                     client.watch(name)
                 
                                     client.multi()
                 
                                     client.zadd(name=name, mapping=data)
                                    
                                     client.execute()
                 
                                     break
                 
                             except WatchError:
                 
                                 logger.warning(f"Alguem ja estava alterando {name}, então a operação vai tentar ser executada novamente!!")
                                 continue


    #Le em formato de sorted set
    async def sorted_get(self, name:str) -> dict|None:


         try:

              logger.info(f"tentando ler {name}...")


              with self.client.pipeline() as client:

                   client.zrange(
                        name=name,
                        start=0,
                        end=99,
                        withscores=True
                   )


                   return client.execute()[0]

         except Exception as e:
              logger.error(e)
              raise RedisControlError(e)


    #Le em forma normal
    async def get(self, name:str) -> dict|None:


         try:
              logger.info(f"Lendo {name}...")

              with self.client.pipeline() as client:

                   client.get(name=name)

                   return client.execute()[0]

         except Exception as e:

              logger.error(e)
              raise RedisControlError(e)


    #Deleta um set por completo, ou por uma chave apenas
    async def delete(self, name:str, user:str|None = None) -> None:

         
            while True:

                 logger.info(f"Deletando {name}..." if user is None else f"Deletando {user} de {name}...")

                 with self.client.pipeline(transaction=True) as client:

                      client.watch(name)

                      client.multi()

                      if user is not None:
                           client.zrem(name, user)

                      else:

                           client.delete(name)

            




    
              

                



         


        
