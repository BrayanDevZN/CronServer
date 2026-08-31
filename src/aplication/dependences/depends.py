"""
Dependencias da aplicação
"""


from src.service.module import control_db, jwt_auth
from fastapi import Request, HTTPException


class DependsIntance:

    #metodo pra pegar os dados do token
    def _get_token(self) -> None:

        self.payload = jwt_auth.read(self.requests.headers["X-instance_token"])


    #Metodo pra verificar se o usuario existe, se não existir, retorna erro
    def exists(self,requests:Request):

        self.requests = requests
        self._get_token()

        instance = control_db.requests.select(public_id=self.payload["public_id"])

        if instance is None:

            raise HTTPException(
                status_code=401,
                detail="not found instance"
            )


        return self.payload 


    

        