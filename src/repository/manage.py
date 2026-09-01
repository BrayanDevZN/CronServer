"""
Junta os modulos e facilita a importação
"""

from src.repository.control.tasks import TasksControl, RedisControl
from src.repository.control.requests import RequestsControl
from sqlalchemy import Engine
from src.repository.control.all import AllDbControl
from redis import Redis

class ControlDb:
    def __init__(self, engine:Engine, redis_connection:Redis)-> None:
        self.tasks = TasksControl(engine=engine, redis_connection=redis_connection)
        self.requests = RequestsControl(engine=engine, redis_connection=redis_connection)
        self.all = AllDbControl(engine=engine, redis_connection=redis_connection)
        
