from src.logs.log import LogLayer
logger = LogLayer("aplication_handles_requests").config().logger()

"""
Rotas de requests
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from src.service.module import control_db, jwt_auth, RequestsModel
from src.aplication.dependences.depends import DependsIntance
router_requests = APIRouter(prefix="/requests")



#Rota pra criar os dados de requests
@router_requests.post("/")
async def insert(request:RequestsModel.RequestsModelCreate):

    try:

        logger.info("Executando rota requests com o metodo POST...")


        instance = await control_db.requests.select(search="url", value=request.url)

        if instance is not None and instance["method"] == request.method:

            return JSONResponse(
                status_code=401,
                content={"error": f"Exists instance of url {request.url}", "status": "failed", "token": None}
            )


        instance = await control_db.requests.insert(url=request.url, headers=request.headers,
                                                    body=request.body, method=request.method, interval=request.interval)

    


        token = jwt_auth.create(payload={"public_id": instance["public_id"], "created_at": instance["created_at"]})


        return JSONResponse(
            status_code=201,
            content={"error": None, "status": "sucess", "token": token}
        )

    except Exception as e:

        return JSONResponse(
            status_code=501,
            content={"error": e, "status": "failed", "token": None}
        )

@router_requests.get("/{instance_token}")
async def select(instance_token:str):

    try:

        logger.info("Executando rota requests com o metodo GET...")

        token = jwt_auth.read(token=instance_token)

        instance = await control_db.requests.select(search="public_id", value=token["public_id"])

        if instance is None:

            return JSONResponse(
                status_code=401,
                content={"error": "instance not found", "content": None}
            )


        return JSONResponse(
                        status_code=201,
                        content={"error": None, "content": instance_token}
                    )

    except Exception as e:

        return JSONResponse(
            status_code=501,
            content={"error": e, "content": None}
        )


@router_requests.patch("/")
async def update(instance: RequestsModel.RequestsModelUpdate, payload: str = Depends(DependsIntance().exists)):

    try:

        logger.info("Executando rota requests com o metodo PATCH...")

        public_id = payload["public_id"]


        await control_db.requests.update(public_id=public_id, set=instance.set, value=instance.value)


        return JSONResponse(content={"status": "sucess", "error": None}, status_code=201)

    except Exception as e:

        return JSONResponse(
            content={"status": "failed", "error": e}, status_code=501
        )


@router_requests.delete("/")
async def delete(payload: str = Depends(DependsIntance().exists)):

    try:

        logger.info("Executando rota requests com o metodo PATCH...")

        await control_db.requests.delete(public_id=payload["public_id"])

        return JSONResponse(content={"status": "sucess", "error": None}, status_code=201)

    except Exception as e:

        return JSONResponse(
            content={"status": "failed", "error": e}, status_code=501
        )















        




    

