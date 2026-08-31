"""Testes de integração das rotas HTTP de requests."""

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
REQUESTS_URL = f"{BASE_URL}/requests"


class TestRequestsRouter(unittest.TestCase):

    def setUp(self) -> None:
        self.tokens: list[str] = []
        self.public_ids: list[str] = []
        self.engine = control_db.requests.db.eng
        self.redis = control_db.requests.client.client

    def tearDown(self) -> None:
        if self.public_ids:
            self.redis.delete(
                *(f"request:{public_id}" for public_id in self.public_ids)
            )

            with self.engine.begin() as session:
                for public_id in self.public_ids:
                    session.execute(
                        text(
                            "delete from requests "
                            "where public_id = :public_id"
                        ),
                        {"public_id": public_id},
                    )

    def _payload(self) -> dict:
        return {
            "url": f"https://example.com/router-test/{uuid4()}",
            "method": "GET",
            "headers": {"Authorization": "Bearer test"},
            "body": {"test": True},
            "interval": 60,
        }

    def _create_instance(self) -> tuple[requests.Response, str]:
        response = requests.post(
            f"{REQUESTS_URL}/",
            json=self._payload(),
            timeout=10,
        )

        self.assertEqual(response.status_code, 201, response.text)

        content = response.json()
        token = content.get("token")

        self.assertEqual(content.get("status"), "sucess")
        self.assertIsNone(content.get("error"))
        self.assertIsInstance(token, str)
        self.assertTrue(token)

        self.tokens.append(token)
        payload = jwt_auth.read(token=token)
        self.public_ids.append(payload["public_id"])
        return response, token

    def _seed_instance(self) -> str:
        public_id = str(uuid4())

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
                    "public_id": public_id,
                    "url": f"https://example.com/router-seed/{uuid4()}",
                },
            ).mappings().one()

            session.execute(
                text("""
                    INSERT INTO cron(instance_id, interval)
                    VALUES(:instance_id, 30)
                """),
                {"instance_id": request["id"]},
            )

        token = jwt_auth.create(
            payload={
                "public_id": public_id,
                "created_at": str(request["created_at"]),
            }
        )
        self.tokens.append(token)
        self.public_ids.append(public_id)
        return token

    def test_post_requests(self) -> None:
        response, _ = self._create_instance()

        self.assertEqual(response.status_code, 201)

    def test_get_requests(self) -> None:
        token = self._seed_instance()

        response = requests.get(
            f"{REQUESTS_URL}/{token}",
            headers={"X-instance_token": token},
            timeout=10,
        )

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json(), {"error": None, "content": token})

    def test_patch_requests(self) -> None:
        token = self._seed_instance()

        response = requests.patch(
            f"{REQUESTS_URL}/",
            headers={"X-instance_token": token},
            json={"set": "interval", "value": "60"},
            timeout=10,
        )

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json(), {"status": "sucess", "error": None})

    def test_delete_requests(self) -> None:
        token = self._seed_instance()

        response = requests.delete(
            f"{REQUESTS_URL}/",
            headers={"X-instance_token": token},
            timeout=10,
        )

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json(), {"status": "sucess", "error": None})


if __name__ == "__main__":
    unittest.main()
