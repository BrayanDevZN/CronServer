"""
Inicializa a aplicação
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.aplication.handles.requests import router_requests
