from src.logs.log import LogLayer
logger = LogLayer("infra_connect_celery").config().logger()



"""
Cria conexão com celery
"""
from celery import Celery
class CeelryConnectError(Exception):
    pass

def celery_connect(backend:str, broker:str) -> Celery:

    try:
        logger.info("Criando conexão com celery...")

        return Celery(
            backend=backend,
            broker=broker
        )

    except Exception as e:
        logger.error(e)
        

