from src.logs.log import LogLayer
logger = LogLayer("domain_jwt").config().logger()


"""
Cria e le os tokens jwt
"""

import jwt

class JwtAuthError(Exception):
    pass


class JwtAuth:

    def __init__(self, sing:str)-> None:

        self.sing = sing
        self.alg = "HS256"


    #Cria o token
    def create(self, payload:dict) -> str:

        try: 

            logger.info("Criando token...")

            return jwt.encode(
                payload=payload,
                algorithm=self.alg,
                key=self.sing
            )

        except Exception as e:

            logger.error(e)
            raise JwtAuthError(e)


    #Le o token e retorna o payload
    def read(self, token:str) -> dict:

        try:  

            logger.info("Lendo token...")

            return jwt.decode(
                algorithms=[self.alg],
                key=self.sing,
                jwt=token
            )

        except Exception as e:

            logger.error(e)
            raise JwtAuthError(e)


        
