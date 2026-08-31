from src.logs.log import LogLayer
logger = LogLayer("aplication_midlleware").config().logger()



"""
Midlleware que confere o rate limit
"""

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from src.service.module import client
from src.infra.manage import envroins
from fastapi import Request



class MIdlleware(BaseHTTPMiddleware):

    async def dispatch(self, request:Request, call_next):

        logger.info("Conferindo global rate limit...")

        instance = await client.get("global_rate_limit")


        if instance > envroins["global_rate_limit"] and instance is not None:

            logger.warning("Limite de requisições excedido!!!")

            return JSONResponse(
                status_code=429,
                content={"error": "exceded global rate limit"}
            )


        client.incr("global_rate_limit")


        if  request.method == "POST" and  request.url.path == "/requests/":

            ip = request.client.host
            instance = await client.get(f"ip?rate_limit:{ip}")
            logger.info("Conferindo rate limit...")

            if instance is not None and  instance > envroins["rate_limit"]:

                logger.warning(f"rate limit ecedido pelo ip {ip}!!")

                return JSONResponse(
                    status_code=429,
                    content={"error": f"exeded limit of ip: {ip}"}
                )

            return await call_next(request)


        if not "X-instance_token" in request.headers:

            return JSONResponse(
                status_code=401, content={"Error": "expeted header X-instance_token"}
            )


        token = request.headers["X-instance_token"]

        logger.info("Conferindo rate limit...")

        instance = await client.get(f"token?rate_limit: {token}")

        if instance is not None and instance > envroins["rate_limit"]:

            logger.warning(f"Exeded rate limit of token {token}!!!")

            return JSONResponse(
                status_code=429,
                content={"Error": f"Exeded rate limit of token {token}!!!"}
            )


        return await call_next(request)








        