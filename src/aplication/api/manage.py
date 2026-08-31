"""
Inicializa a api
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.aplication.api.handles.requests import router_requests
from src.aplication.api.handles.tasks import router_tasks
from src.aplication.api.midlleware.base import MIdlleware
from src.infra.manage import envroins

class InstanceAPI:

    def __init__(self)-> None:

        self.routes= [router_requests, router_tasks]
        self.app = FastAPI()

    #Cria as configurações de cors
    def _cors(self) -> None:

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=[envroins["origin"]],
            allow_methods=["*"],
            allow_credentials=["X-instance_token"]
        )

    #Adiciona o midlleware
    def _mid(self) -> None:

        self.app.add_middleware(MIdlleware)


    #Adiciona as rotas
    def _routes(self) -> None:

        for router in self.routes:

            self.app.include_router(router)


    #roda todos os metodos
    def run(self) -> FastAPI:

        self._cors()
        self._mid()
        self._routes()

        return self.app


