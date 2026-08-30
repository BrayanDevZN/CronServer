"""
Junta as conexões de redis e banco de dados com a classe de repository
"""
from src.infra.manage import client, engine
from src.repository.manage import ControlDb, RedisControl

control_db = ControlDb(engine=engine, redis_connection=client)

client = RedisControl(connection=client)