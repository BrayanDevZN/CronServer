"""Teste de integração da task executada pelo worker do Celery."""

import asyncio
import sys
import threading
import unittest
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent

# Impede que este arquivo seja importado no lugar do módulo da aplicação.
sys.path = [
    path
    for path in sys.path
    if Path(path or ".").resolve() != TESTS_DIR
]
sys.path.insert(0, str(PROJECT_ROOT))

from src.aplication.tasks.task import execute_task
from src.service.db import control_db
from sqlalchemy import text


class JsonHandler(BaseHTTPRequestHandler):

    def do_GET(self) -> None:
        body = b'{"status": "ok"}'

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass


class TestExecuteTaskWorker(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = control_db.requests.db.eng
        self.redis = control_db.requests.client.client

        self.http_server = ThreadingHTTPServer(("127.0.0.1", 0), JsonHandler)
        self.http_thread = threading.Thread(
            target=self.http_server.serve_forever,
            daemon=True,
        )
        self.http_thread.start()

        host, port = self.http_server.server_address
        self.url = f"http://{host}:{port}/task-test/{uuid4()}"
        self.public_id = uuid4()

        with self.engine.begin() as session:
            request = session.execute(
                text("""
                    INSERT INTO requests(
                        public_id, url, method, headers, body
                    )
                    VALUES(
                        :public_id, :url, 'GET', '{}'::jsonb, '{}'::jsonb
                    )
                    RETURNING id
                """),
                {"public_id": self.public_id, "url": self.url},
            ).mappings().one()

            self.instance_id = request["id"]

            cron = session.execute(
                text("""
                    INSERT INTO cron(instance_id, interval, created_at)
                    VALUES(
                        :instance_id,
                        30,
                        CURRENT_TIMESTAMP - INTERVAL '1 day'
                    )
                    RETURNING id, created_at
                """),
                {"instance_id": self.instance_id},
            ).mappings().one()

            self.cron_id = cron["id"]
            self.previous_created_at = cron["created_at"]

    def tearDown(self) -> None:
        self.redis.delete(
            f"request:{self.instance_id}",
            f"request:{self.public_id}",
            f"task:instance_id:{self.instance_id}",
        )

        with self.engine.begin() as session:
            session.execute(
                text("DELETE FROM requests WHERE id = :instance_id"),
                {"instance_id": self.instance_id},
            )

        self.http_server.shutdown()
        self.http_server.server_close()
        self.http_thread.join(timeout=2)

    def test_worker_updates_cron_and_saves_result(self) -> None:
        instance = asyncio.run(
            control_db.requests.select(
                search="id",
                value=self.instance_id,
            )
        )

        task_result = execute_task.delay(instance)

        try:
            result = task_result.get(timeout=20, propagate=True)

            self.assertIsNone(result)
            self.assertEqual(task_result.state, "SUCCESS")

            with self.engine.connect() as session:
                cron_created_at = session.execute(
                    text("""
                        SELECT created_at
                        FROM cron
                        WHERE id = :cron_id
                    """),
                    {"cron_id": self.cron_id},
                ).scalar_one()

                saved_task = session.execute(
                    text("""
                        SELECT result
                        FROM tasks
                        WHERE instance_id = :instance_id
                          AND cron_id = :cron_id
                        ORDER BY created_at DESC
                        LIMIT 1
                    """),
                    {
                        "instance_id": self.instance_id,
                        "cron_id": self.cron_id,
                    },
                ).scalar_one()

            self.assertGreater(cron_created_at, self.previous_created_at)
            self.assertLessEqual(cron_created_at, datetime.now(timezone.utc))
            self.assertEqual(saved_task, "success")
        finally:
            task_result.forget()


if __name__ == "__main__":
    unittest.main()
