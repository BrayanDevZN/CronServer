"""
Junta os modulos de infra e facilita a importação
"""



#Pega as variaveis de ambiente
from src.infra.core.settings  import ConfigEnviroin
config = ConfigEnviroin()
envroins = config.get()


#Junta a classe que faz conexão com banco de dados com a variavel de ambiente requerida
from src.infra.connect.db import ConnectDb
engine = ConnectDb(url=envroins["url"]).run()



#Junta a classe de conexão com redis com suas variaveis
from src.infra.connect.redis import RedisConnect
client = RedisConnect(port=envroins["redis_port"], host=envroins["redis_host"]).run()





if __name__ == "__main__":

    import sys


    #Executa migration do redis
    if sys.argv[1] == "migration_redis":

        from src.infra.migration.redis import MigrationRedis

        instance = MigrationRedis(engine=engine, redis_connection=client)
        instance.run()


    #Executa a migração do banco de dados
    elif sys.argv[1] == "migration_db":

        from src.infra.migration.db import MigrationDb

        instance = MigrationDb(engine=engine)

        instance.run()

    else:

        raise ValueError(f"Not expeted argument {sys.argv[1]}")

    