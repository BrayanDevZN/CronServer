from src.logs.log import LogLayer
logger = LogLayer("infra_connect_db").config().logger()



"""
Cria a engine do banco de dados
"""

from sqlalchemy import Engine, create_engine, text


class ConnectDbError(Exception):
    pass


class ConnectDb:

    def __init__(self, url:str)-> None:
        self.url = url


    #Cria a engine
    def _engine(self) -> None:

        try:

            logger.info("Criando a conexão com banco de dados...")

            self.eng = create_engine(self.url)


        except Exception as e:

            logger.error(e)
            ConnectDbError(e)

    #Faz o teste
    def _test(self) -> None:

        try:

            logger.info("Fazendo teste na conexão com banco de dados...")

            with self.eng.begin() as session:

                session.execute(text("SELECT 1;"))

        except Exception as e:
            logger.error(e)
            ConnectDbError(e)


    #Executa os metodos e retorna a engine
    def run(self) -> Engine:

        self._engine()
        self._test()

        return self.eng

