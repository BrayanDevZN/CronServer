"""
Pega as variaveis de ambiente
"""


class NotFoundEnviroin(Exception):
    pass

from pathlib import Path
import os

class ConfigEnviroin:

    def __init__(self)-> None:

        self.envs = ["url", "redis_port", "redis_host", "sing"]
        self.BASE_DIR = Path(__file__).resolve().parent


    #Carrega as variaveis de ambiente se o .env existir
    def _load(self) -> None:

        path = self.BASE_DIR / ".env"

        if os.path.exists(path):

            from dotenv import load_dotenv
            load_dotenv(path)


    #Le as variaveis de ambiente de self.envs
    def _env(self) -> None:

        envs = {}

        for env_name in self.envs:

            env = os.getenv(env_name)

            if env is None:

                raise NotFoundEnviroin(f"Not found envroin {env_name}")

            envs[env_name] = env

        self.envs = envs

    #Executa os metodos e retorna as variaveis num dict
    def get(self) -> dict:

        self._load()
        self._env()
        return self.envs




    





    
        
