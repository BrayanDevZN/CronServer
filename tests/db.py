"""Testes de todos os métodos da instância compartilhada de ControlDb."""

import sys
import unittest
from pathlib import Path
from uuid import uuid4


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent

sys.path = [
    path
    for path in sys.path
    if Path(path or ".").resolve() != TESTS_DIR
]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from src.service.db import control_db


class TestControlDb(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        test_id = uuid4()
        self.public_id = uuid4()
        self.url = f"https://example.com/control-db/{test_id}"
        self.insert_url = f"https://example.com/control-db/insert/{test_id}"
        self.engine = control_db.requests.db.eng
        self.redis = control_db.requests.client.client

        with self.engine.begin() as session:
            request = session.execute(
                text(
                    "insert into requests(public_id, url, method, headers, body) "
                    "values("
                    ":public_id, :url, :method, "
                    "cast(:headers as jsonb), cast(:body as jsonb)"
                    ") returning id"
                ),
                {
                    "public_id": self.public_id,
                    "url": self.url,
                    "method": "GET",
                    "headers": '{"Authorization": "Bearer test"}',
                    "body": '{"test": true}',
                },
            ).fetchone()

            self.instance_id = request[0]

            cron = session.execute(
                text(
                    "insert into cron(instance_id, interval) "
                    "values(:instance_id, :interval) returning id"
                ),
                {"instance_id": self.instance_id, "interval": 30},
            ).fetchone()

            self.cron_id = cron[0]

            task = session.execute(
                text(
                    "insert into tasks(instance_id, cron_id, result) "
                    "values(:instance_id, :cron_id, :result) returning id"
                ),
                {
                    "instance_id": self.instance_id,
                    "cron_id": self.cron_id,
                    "result": "scheduled",
                },
            ).fetchone()

            self.task_id = task[0]

    def tearDown(self) -> None:
        with self.engine.begin() as session:
            public_ids = session.execute(
                text(
                    "select public_id from requests "
                    "where url in (:url, :insert_url)"
                ),
                {"url": self.url, "insert_url": self.insert_url},
            ).scalars().all()

            cache_keys = [
                *(f"request:{public_id}" for public_id in public_ids),
                f"task:instance_id:{self.instance_id}",
            ]
            self.redis.delete(*cache_keys)

            session.execute(
                text("delete from requests where url in (:url, :insert_url)"),
                {"url": self.url, "insert_url": self.insert_url},
            )

    async def test_requests_insert(self) -> None:
        result = await control_db.requests.insert(
            url=self.insert_url,
            method="POST",
            headers={"Content-Type": "application/json"},
            body={"test": True},
            interval=60,
        )

        self.assertEqual(result["url"], self.insert_url)
        self.assertEqual(result["interval"], 60)

    async def test_requests_select(self) -> None:
        result = await control_db.requests.select(public_id=str(self.public_id))

        self.assertIsNotNone(result)
        self.assertEqual(str(result["public_id"]), str(self.public_id))

    async def test_requests_update(self) -> None:
        result = await control_db.requests.update(
            public_id=str(self.public_id),
            set="interval",
            value=90,
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["interval"], 90)

    async def test_requests_delete(self) -> None:
        await control_db.requests.delete(public_id=str(self.public_id))

        with self.engine.connect() as session:
            exists = session.execute(
                text("select 1 from requests where public_id = :public_id"),
                {"public_id": self.public_id},
            ).fetchone()

        self.assertIsNone(exists)

    async def test_tasks_insert(self) -> None:
        result = await control_db.tasks.insert(
            instance_id=self.instance_id,
            cron_id=self.cron_id,
            result="success",
        )

        self.assertEqual(result["instance_id"], self.instance_id)
        self.assertEqual(result["result"], "success")

    async def test_tasks_select(self) -> None:
        result = await control_db.tasks.select(instance_id=self.instance_id)

        self.assertIsNotNone(result)
        self.assertEqual(result["instance_id"], self.instance_id)
        self.assertEqual(result["result"], "scheduled")

    async def test_tasks_update(self) -> None:
        result = await control_db.tasks.update(
            instance_id=self.instance_id,
            result="success",
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["result"], "success")

    async def test_tasks_delete(self) -> None:
        await control_db.tasks.delete(instance_id=self.instance_id)

        with self.engine.connect() as session:
            exists = session.execute(
                text("select 1 from tasks where instance_id = :instance_id"),
                {"instance_id": self.instance_id},
            ).fetchone()

        self.assertIsNone(exists)


if __name__ == "__main__":
    unittest.main()
