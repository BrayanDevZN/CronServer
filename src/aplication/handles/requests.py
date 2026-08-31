from src.logs.log import LogLayer
logger = LogLayer("aplication_handles_requests").config().logger()

"""
Rotas de requests
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from src.service.module import control_db, jwt_auth

router_requests = APIRouter(prefix="/requests")



#Rota pra criar os dados de requests
@router_requests.post("/")
def insert()

