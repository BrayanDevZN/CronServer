"""
Junta os modulos de infra e facilita a importação
"""



#Pega as variaveis de ambiente
from src.infra.core.settings  import ConfigEnviroin
config = ConfigEnviroin()
envroins = config.get()
