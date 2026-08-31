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