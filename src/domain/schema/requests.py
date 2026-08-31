"""
Schema de requests
"""

from pydantic import BaseModel
from typing import Literal
class RequestsModelCreate(BaseModel):

    url:str
    method: Literal["POST", "GET", "PATCH", "PUT", "DELETE"]
    body:dict|str
    headers:dict|str



class RequestsModelUpdate(BaseModel):
    set:Literal["method", "headers", "body", "interval"]
    value:str