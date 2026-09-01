from src.logs.log import LogLayer
logger = LogLayer("aplication_tasks_execute").config().logger()




"""
Faz a requisição desejada e atualiza created at do cron
"""

from datetime import datetime, timezone
from src.service.module import control_db, client, HttpRequest


class ExecuteTask:

    def __init__(self, instance_id:int)-> None:

        self.instance_id = instance_id
       

    #Pega os dados da instancia
    async def _get(self) -> None:

        self.result = await  control_db.requests.select(search="id", value=self.instance_id)

    #Verifica se existe
    async def _exists(self) -> None:

        self.exists = self.result is not None

    #Executa a requisição
    async def _request(self) -> None:

        countdown = 0

        while True:

            try:

                instance = HttpRequest(url=self.result["url"], method=self.result["method"], headers=self.result["headers"],
                                       body=self.result["body"]
                                       )


                self.request = instance.run()

            except Exception:

                if countdown <=3:
                    countdown +=1
                    continue

                else:

                    self.request = None

    #Atualiza o created_at
    async def _update(self) -> None:

        now = datetime.now(timezone.utc)

        await control_db.requests.update(public_id=self.result["public_id"], set="created_at", value=now)


    #Salva o resultado
    async def _save(self) -> None:

        

        await control_db.tasks.insert(instance_id=self.instance_id, cron_id=self.result["cron_id"], 
                                      result="sucess" if self.result is not None else "failed")


    #Executa todos metodos
    async def run(self) -> None:

        await self._get()
        await self._exists()

        if self.exists:

            await self._request()
            await self._update()
            await self._save()


    

    

                


                

    



    

    
    