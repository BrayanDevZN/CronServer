"""Testes do executor de requisições HTTP."""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.infra.request import HttpRequest, HttpRequestError


class TestHttpRequest(unittest.TestCase):

    @patch("src.infra.request.requests.request")
    def test_run_executes_request_with_all_parameters(self, request_mock: Mock) -> None:
        response = Mock(status_code=201)
        request_mock.return_value = response

        result = HttpRequest(
            url="https://example.com/tasks",
            method="post",
            headers={"Authorization": "Bearer token"},
            body={"task": "example"},
        ).run()

        request_mock.assert_called_once_with(
            method="POST",
            url="https://example.com/tasks",
            headers={"Authorization": "Bearer token"},
            json={"task": "example"},
        )
        self.assertIs(result, response)

    @patch("src.infra.request.requests.request")
    def test_run_rejects_invalid_method(self, request_mock: Mock) -> None:
        with self.assertRaises(HttpRequestError):
            HttpRequest(
                url="https://example.com/tasks",
                method="invalid",
            ).run()

        request_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
