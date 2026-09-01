"""
Inicializa a aplicação
"""


#Inicia a api
from src.aplication.api.manage import InstanceAPI
app = InstanceAPI().run()




#Inica o cron loop
if __name__ == "__main__":

    import sys

    if sys.argv[1] == "start_cron":

        from src.aplication.cron.manage import cron_loop
        import asyncio
        asyncio(cron_loop())

    else:

        raise ValueError(f"Not expeted argument {sys.argv[1]}")