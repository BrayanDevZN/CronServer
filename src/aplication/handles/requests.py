from src.logs.log import LogLayer
logger = LogLayer("aplication_handles_requests").config().logger()

"""
Rotas de requests
"""

from fastapi import APIRouter

