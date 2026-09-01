"""
Cria a configuração de logs por camada
"""

import logging
from pathlib import Path


class LogLayer:

    FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    COLORS = {
        "black": "30",
        "red": "31",
        "green": "32",
        "yellow": "33",
        "blue": "34",
        "magenta": "35",
        "cyan": "36",
        "white": "37",
    }

    def __init__(self, layer: str, color: str | None = None) -> None:
        # Caminho base
        self.BASE_DIR = Path(__file__).resolve().parent

        # Camada
        self.layer = layer
        self.color = color
        self._logger = logging.getLogger(layer)

    #Adiciona o nome da camada no caminho
    def _path(self) -> None:
        self.path = self.BASE_DIR / f"{self.layer}.log"

    #Pega as configurações de log
    def config(self) -> "LogLayer":
        self._path()

        self._logger.setLevel(logging.INFO)
        self._logger.propagate = False

        file_formatter = logging.Formatter(self.FORMAT)

        console_format = self.FORMAT

        if self.color is not None:
            color_code = self.COLORS.get(self.color.lower())

            if color_code is None:
                available_colors = ", ".join(self.COLORS)
                raise ValueError(
                    f"Cor inválida: {self.color}. "
                    f"Cores disponíveis: {available_colors}"
                )

            colored_message = f"\033[{color_code}m%(message)s\033[0m"
            console_format = (
                "%(asctime)s | %(levelname)s | %(name)s | "
                f"{colored_message}"
            )

        console_formatter = logging.Formatter(console_format)

        file_exists = any(
            isinstance(handler, logging.FileHandler)
            and Path(handler.baseFilename) == self.path
            for handler in self._logger.handlers
        )

        if not file_exists:
            file_handler = logging.FileHandler(self.path, encoding="utf-8")
            file_handler.setFormatter(file_formatter)
            self._logger.addHandler(file_handler)

        console_handler = next(
            (
                handler
                for handler in self._logger.handlers
                if getattr(handler, "_log_layer_console", False)
            ),
            None,
        )

        if console_handler is None:
            console_handler = logging.StreamHandler()
            console_handler._log_layer_console = True
            self._logger.addHandler(console_handler)

        console_handler.setFormatter(console_formatter)

        return self

    #Retorna uma variavel carregando as configurações
    def logger(self) -> logging.Logger:
        return self._logger
