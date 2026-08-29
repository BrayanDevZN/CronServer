"""Executa requisições HTTP configuradas pelo usuário."""

import requests

from src.logs.log import LogLayer


logger = LogLayer("infra_request").config().logger()


class HttpRequestError(Exception):
    pass


class HttpRequest:

    METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}

    def __init__(
        self,
        url: str,
        method: str,
        headers: dict[str, str] | None = None,
        body: dict | None = None,
    ) -> None:
        self.url = url
        self.method = method.upper()
        self.headers = headers or {}
        self.body = body

    def _validate(self) -> None:
        if not self.url:
            raise HttpRequestError("A URL não pode estar vazia")

        if self.method not in self.METHODS:
            raise HttpRequestError(f"Método HTTP não suportado: {self.method}")

    def _request(self) -> None:
        try:
            logger.info("Executando requisição %s para %s", self.method, self.url)

            self.response = requests.request(
                method=self.method,
                url=self.url,
                headers=self.headers,
                json=self.body,
            )

            logger.info(
                "Requisição concluída com status %s",
                self.response.status_code,
            )

        except requests.RequestException as error:
            logger.error("Falha ao executar a requisição: %s", error)
            raise HttpRequestError(error) from error

    def run(self) -> requests.Response:
        self._validate()
        self._request()
        return self.response
