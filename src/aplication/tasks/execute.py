from src.logs.log import LogLayer
logger = LogLayer("aplication_tasks_execute").config().logger()




"""
Faz a requisição desejada e atualiza created at do cron
"""

from datetime import datetime, timezone
import json
from src.service.module import control_db, client, HttpRequest


class ExecuteTask:

    def __init__(self, instance_id:int)-> None:

        self.instance_id = instance_id
       

    #Executa a requisição
    async def _request(self) -> None:

        countdown = 0

        while True:

            try:

                headers = self.result["headers"]
                body = self.result["body"]

                if isinstance(headers, str):
                    headers = json.loads(headers)

                if isinstance(body, str):
                    body = json.loads(body)

                instance = HttpRequest(url=self.result["url"], method=self.result["method"], headers=headers,
                                       body=body
                                       )


                self.request = instance.run()
                return

            except Exception as error:

                countdown += 1
                logger.warning("Tentativa %s falhou: %s", countdown, error)

                if countdown < 4:
                    continue

                else:

                    self.request = None
                    return

    #Atualiza o created_at
    async def _update(self) -> None:

        now = datetime.now(timezone.utc)

        await control_db.requests.update(public_id=self.result["public_id"], set="created_at", value=now)


    #Salva o resultado
    async def _save(self) -> None:

        

        await control_db.tasks.insert(instance_id=self.instance_id, cron_id=self.result["cron_id"], 
                                      result="success" if self.request is not None else "failed")


    #Executa todos metodos
    async def run(self) -> None:

        
            await self._request()
            await self._update()
            await self._save()
