from src.logs.log import LogLayer
logger = LogLayer("aplication_handles_tasks").config().logger()


"""
Executa rota /tasks
"""


from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from src.service.module import control_db
from src.aplication.api.dependences.depends import DependsIntance


router_tasks = APIRouter(prefix="/tasks", tags=["tasks"])


@router_tasks.get("/")
async def select(payload:dict = Depends(DependsIntance().exists)):

    try:


        logger.info("Executando rota requests com o metodo POST...")

        instance_id = payload["id"]
        result =await control_db.tasks.select(instance_id=instance_id)

        return JSONResponse(
            content={"error": None, "content": result}, status_code=201
        )

    except Exception as e:

        return JSONResponse(
            content={"error": e, "content": None}
        )


