"""Teste manual da classe responsável pela configuração de logs."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.logs.log import LogLayer


def test_log_layer() -> None:
    logger = LogLayer("test").config().logger()
    logger.info("Teste da classe LogLayer")


if __name__ == "__main__":
    test_log_layer()
