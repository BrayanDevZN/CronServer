"""
Cria a configuração de logs por camada
"""

import logging
from pathlib import Path


class LogLayer:

    FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

    def __init__(self, layer: str) -> None:
        # Caminho base
        self.BASE_DIR = Path(__file__).resolve().parent

        # Camada
        self.layer = layer
        self._logger = logging.getLogger(layer)

    #Adiciona o nome da camada no caminho
    def _path(self) -> None:
        self.path = self.BASE_DIR / f"{self.layer}.log"

    #Pega as configurações de log
    def config(self) -> "LogLayer":
        self._path()

        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        formatter = logging.Formatter(self.FORMAT)

        file_exists = any(
            isinstance(handler, logging.FileHandler)
            and Path(handler.baseFilename) == self.path
            for handler in self._logger.handlers
        )

        if not file_exists:
            file_handler = logging.FileHandler(self.path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

        console_exists = any(
            getattr(handler, "_log_layer_console", False)
            for handler in self._logger.handlers
        )

        if not console_exists:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler._log_layer_console = True
            self._logger.addHandler(console_handler)

        return self

    #Retorna uma variavel carregando as configurações
    def logger(self) -> logging.Logger:
        return self._logger
