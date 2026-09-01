"""Teste de ponta a ponta das rotas da aplicação em execução."""

import os
import unittest
from uuid import uuid4

import requests
from requests.exceptions import JSONDecodeError


BASE_URL = os.getenv("CRON_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")
TIMEOUT = float(os.getenv("CRON_SERVER_TIMEOUT", "15"))


class TestApplication(unittest.TestCase):

    def setUp(self) -> None:
        self.client = requests.Session()
        self.token: str | None = None

    def tearDown(self) -> None:
        if self.token is not None:
            try:
                self.client.delete(
                    f"{BASE_URL}/requests/",
                    headers=self._headers(),
                    timeout=TIMEOUT,
                )
            except requests.RequestException:
                pass

        self.client.close()

    def _headers(self) -> dict[str, str]:
        if self.token is None:
            return {}

        return {"X-instance_token": self.token}

    def _json(self, response: requests.Response) -> dict:
        try:
            return response.json()
        except JSONDecodeError as error:
            self.fail(
                f"A API retornou conteúdo que não é JSON: "
                f"status={response.status_code}, body={response.text!r}"
            )
            raise error

    def test_complete_application_flow(self) -> None:
        identifier = uuid4()
        request_payload = {
            "url": f"https://httpbin.org/anything/cron-server-{identifier}",
            "method": "GET",
            "headers": {"X-E2E-Test": str(identifier)},
            "body": {},
            "interval": 1,
        }

        create_response = self.client.post(
            f"{BASE_URL}/requests/",
            json=request_payload,
            timeout=TIMEOUT,
        )
        create_content = self._json(create_response)

        self.assertEqual(create_response.status_code, 201, create_response.text)
        self.assertEqual(create_content.get("status"), "sucess")
        self.assertIsNone(create_content.get("error"))
        self.assertIsInstance(create_content.get("token"), str)
        self.assertTrue(create_content["token"])
        self.token = create_content["token"]
        print("[OK] Agendamento criado")

        get_response = self.client.get(
            f"{BASE_URL}/requests/{self.token}",
            headers=self._headers(),
            timeout=TIMEOUT,
        )
        get_content = self._json(get_response)

        self.assertEqual(get_response.status_code, 201, get_response.text)
        self.assertIsNone(get_content.get("error"))
        self.assertEqual(get_content.get("content"), self.token)
        print("[OK] Agendamento consultado")

        update_response = self.client.patch(
            f"{BASE_URL}/requests/",
            headers=self._headers(),
            json={"set": "interval", "value": "2"},
            timeout=TIMEOUT,
        )
        update_content = self._json(update_response)

        self.assertEqual(update_response.status_code, 201, update_response.text)
        self.assertEqual(update_content.get("status"), "sucess")
        self.assertIsNone(update_content.get("error"))
        print("[OK] Agendamento atualizado")

        tasks_response = self.client.get(
            f"{BASE_URL}/tasks/",
            headers=self._headers(),
            timeout=TIMEOUT,
        )
        tasks_content = self._json(tasks_response)

        self.assertEqual(tasks_response.status_code, 201, tasks_response.text)
        self.assertIsNone(tasks_content.get("error"))
        self.assertTrue(
            tasks_content.get("content") is None
            or isinstance(tasks_content.get("content"), dict)
        )
        print("[OK] Histórico de execuções consultado")

        delete_response = self.client.delete(
            f"{BASE_URL}/requests/",
            headers=self._headers(),
            timeout=TIMEOUT,
        )
        delete_content = self._json(delete_response)

        self.assertEqual(delete_response.status_code, 201, delete_response.text)
        self.assertEqual(delete_content.get("status"), "sucess")
        self.assertIsNone(delete_content.get("error"))
        print("[OK] Agendamento excluído")

        deleted_response = self.client.get(
            f"{BASE_URL}/requests/{self.token}",
            headers=self._headers(),
            timeout=TIMEOUT,
        )

        self.assertEqual(deleted_response.status_code, 401, deleted_response.text)
        self.token = None
        print("[OK] Exclusão confirmada")


if __name__ == "__main__":
    unittest.main(verbosity=2)
