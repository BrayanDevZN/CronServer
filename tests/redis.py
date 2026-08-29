"""Testes de todos os métodos da instância compartilhada de Redis."""

import sys
import unittest
from pathlib import Path
from uuid import uuid4


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent

# Impede que este arquivo seja importado no lugar do pacote externo `redis`.
sys.path = [
    path
    for path in sys.path
    if Path(path or ".").resolve() != TESTS_DIR
]
sys.path.insert(0, str(PROJECT_ROOT))

from src.service.db import client


class TestRedisClient(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        test_id = uuid4()
        self.counter_key = f"test:redis:counter:{test_id}"
        self.hash_key = f"test:redis:hash:{test_id}"
        self.sorted_set_key = f"test:redis:sorted-set:{test_id}"

    def tearDown(self) -> None:
        client.client.delete(
            self.counter_key,
            self.hash_key,
            self.sorted_set_key,
        )

    async def test_incr_and_get(self) -> None:
        await client.incr(name=self.counter_key, time=60)

        result = await client.get(name=self.counter_key)

        self.assertEqual(result, "1")

    async def test_hash(self) -> None:
        data = {"name": "brayan", "status": "scheduled"}

        await client.hash(name=self.hash_key, data=data, time=60)

        self.assertEqual(client.client.hgetall(self.hash_key), data)

    async def test_sorted_set_and_sorted_get(self) -> None:
        await client.sorted_set(
            name=self.sorted_set_key,
            data={"brayan": 1000, "joao": 2000},
        )

        result = await client.sorted_get(name=self.sorted_set_key)

        self.assertEqual(result, [("brayan", 1000.0), ("joao", 2000.0)])

    async def test_delete_key(self) -> None:
        await client.incr(name=self.counter_key, time=60)

        await client.delete(name=self.counter_key)

        self.assertIsNone(await client.get(name=self.counter_key))

    async def test_delete_sorted_set_member(self) -> None:
        await client.sorted_set(
            name=self.sorted_set_key,
            data={"brayan": 1000, "joao": 2000},
        )

        await client.delete(name=self.sorted_set_key, user="brayan")

        result = await client.sorted_get(name=self.sorted_set_key)
        self.assertEqual(result, [("joao", 2000.0)])


if __name__ == "__main__":
    unittest.main()
