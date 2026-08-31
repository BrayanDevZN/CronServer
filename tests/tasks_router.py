"""Teste de integração da rota de consulta de tasks."""

import os
import sys
import unittest
from pathlib import Path
from uuid import uuid4

import requests
from sqlalchemy import text


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
sys.path = [
    path
    for path in sys.path
    if Path(path or ".").resolve() != TESTS_DIR
]
sys.path.insert(0, str(PROJECT_ROOT))

from src.service.module import control_db, jwt_auth


BASE_URL = os.getenv("CRON_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")
TASKS_URL = f"{BASE_URL}/tasks"


class TestTasksRouter(unittest.TestCase):

    def setUp(self) -> None:
        self.public_id = str(uuid4())
        self.engine = control_db.requests.db.eng
        self.redis = control_db.requests.client.client

        with self.engine.begin() as session:
            request = session.execute(
                text("""
                    INSERT INTO requests(
                        public_id, url, method, headers, body
                    )
                    VALUES(
                        :public_id,
                        :url,
                        'GET',
                        '{}'::jsonb,
                        '{}'::jsonb
                    )
                    RETURNING id, created_at
                """),
                {
                    "public_id": self.public_id,
                    "url": f"https://example.com/tasks-router/{uuid4()}",
                },
            ).mappings().one()

            self.instance_id = request["id"]

            cron_id = session.execute(
                text("""
                    INSERT INTO cron(instance_id, interval)
                    VALUES(:instance_id, 30)
                    RETURNING id
                """),
                {"instance_id": self.instance_id},
            ).scalar_one()

            session.execute(
                text("""
                    INSERT INTO tasks(instance_id, cron_id, result)
                    VALUES(:instance_id, :cron_id, :result)
                """),
                {
                    "instance_id": self.instance_id,
                    "cron_id": cron_id,
                    "result": "success",
                },
            )

        self.token = jwt_auth.create(
            payload={
                "public_id": self.public_id,
                "created_at": str(request["created_at"]),
            }
        )

    def tearDown(self) -> None:
        self.redis.delete(
            f"request:{self.public_id}",
            "request:public_id",
            f"task:instance_id:{self.instance_id}",
        )

        with self.engine.begin() as session:
            session.execute(
                text("delete from requests where public_id = :public_id"),
                {"public_id": self.public_id},
            )

    def test_get_tasks_results(self) -> None:
        response = requests.get(
            f"{TASKS_URL}/",
            headers={"X-instance_token": self.token},
            timeout=10,
        )

        self.assertEqual(response.status_code, 201, response.text)

        content = response.json()
        self.assertIsNone(content.get("error"))
        self.assertIsInstance(content.get("content"), dict)
        self.assertEqual(content["content"]["result"], "success")


if __name__ == "__main__":
    unittest.main()
