from src.logs.log import LogLayer
logger = LogLayer("aplication_tasks_execute", color="magenta").config().logger()




"""
Faz a requisição desejada e atualiza created at do cron
"""

from datetime import datetime, timezone
import json
from src.service.module import control_db, HttpRequest


class ExecuteTask:

    def __init__(self, instance:dict)-> None:

        self.instance_id = int(instance["id"])
        self.public_id = instance["public_id"]
        self.cron_id = int(instance["cron_id"])
        self.url = instance["url"]
        self.method = instance["method"]
        self.headers = instance["headers"]
        self.body = instance["body"]
       

    #Executa a requisição
    async def _request(self) -> None:

        countdown = 0

        while True:

            try:

                headers = self.headers
                body = self.body

                if isinstance(headers, str):
                    headers = json.loads(headers)

                if isinstance(body, str):
                    body = json.loads(body)

                instance = HttpRequest(url=self.url, method=self.method, headers=headers,
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

   
    #Salva o resultado
    async def _save(self) -> None:

        

        await control_db.tasks.insert(instance_id=self.instance_id, cron_id=self.cron_id,
                                      result="success" if self.request is not None else "failed")


    #Executa todos metodos
    async def run(self) -> None:

            
            await self._request()
            await self._save()
