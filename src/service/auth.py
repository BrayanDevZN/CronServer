"""
Importa a variavel de ambiente sing e junta com a classe jwtAuth
"""

from src.infra.manage import envroins
from src.domain.module import JwtAuth, RequestsModel


jwt_auth = JwtAuth(sing=envroins["sing"])