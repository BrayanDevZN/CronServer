"""
Cria a configuração de logs por camada
"""

import logging
from pathlib import Path

class LogLayer:

    def __init__(self, layer:str)-> None:


        #Caminho base
        self.BASE_DIR = Path(__file__).resolve().parent 

        #Camada
        self.layer = layer


    #Adiciona o nome da camada no caminho
    def _path(self) -> None:

        self.path = self.BASE_DIR / f"{self.layer}.log"


    #Pega as configurações de log
    def config(self) -> LogLayer:
        self._path()

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            handlers=[
                logging.FileHandler(self.path),
                logging.StreamHandler()
            ]
        )

        return self

    #Retorna uma variavel carregando as configurações
    def logger(self) -> logging:

        return logging.getLogger(self.layer)

        



        