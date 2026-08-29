"""Teste manual das conexões com PostgreSQL e Redis."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from src.infra.connect.db import ConnectDb
from src.infra.connect.redis import RedisConnect
from src.infra.core.settings import ConfigEnviroin


def test_db_connection(envroins: dict) -> None:
    engine = ConnectDb(url=envroins["url"]).run()

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1;"))
            assert result.scalar_one() == 1
    finally:
        engine.dispose()


def test_redis_connection(envroins: dict) -> None:
    client = RedisConnect(
        port=envroins["redis_port"],
        host=envroins["redis_host"],
    ).run()

    try:
        assert client.ping() is True
    finally:
        client.close()


def main() -> None:
    envroins = ConfigEnviroin().get()
    tests = (
        ("PostgreSQL", test_db_connection),
        ("Redis", test_redis_connection),
    )
    failures = []

    for name, test in tests:
        try:
            test(envroins)
            print(f"[OK] Conexão com {name}")
        except Exception as error:
            failures.append(name)
            print(f"[ERRO] Conexão com {name}: {error}")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
