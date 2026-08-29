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


