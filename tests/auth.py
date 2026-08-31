"""Testes da instância compartilhada de autenticação JWT."""

import sys
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent

sys.path = [
    path
    for path in sys.path
    if Path(path or ".").resolve() != TESTS_DIR
]
sys.path.insert(0, str(PROJECT_ROOT))

from domain.auth.jwt import JwtAuthError
from src.service.module import jwt_auth


class TestJwtAuth(unittest.TestCase):

    def test_create_and_read_token(self) -> None:
        payload = {
            "sub": "brayan",
            "role": "admin",
        }

        token = jwt_auth.create(payload=payload)
        decoded_payload = jwt_auth.read(token=token)

        self.assertIsInstance(token, str)
        self.assertEqual(decoded_payload, payload)

    def test_read_rejects_invalid_token(self) -> None:
        with self.assertRaises(JwtAuthError):
            jwt_auth.read(token="invalid-token")


if __name__ == "__main__":
    unittest.main()
