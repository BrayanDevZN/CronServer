from src.logs.log import LogLayer
logger = LogLayer("infra_migration_db", color="green").config().logger()


"""
Cria as tabelas do banco de dados se não existir
"""

class MigrationDbError(Exception):
    pass

from sqlalchemy import Engine, text

class MigrationDb:

    def __init__(self, engine:Engine)-> None:

        self.eng = engine

    #Cria a extensão usada para gerar UUID automaticamente
    def _uuid_extension(self) -> None:

        try:

            logger.info("Criando extensão uuid-ossp se não existir...")

            with self.eng.begin() as session:

                session.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))

        except Exception as e:

            logger.error(e)
            raise MigrationDbError(e)

    #comandos sqls de cada tabela
    def _sql(self) -> None:

        self.sql = {
            "requests": text("""
                CREATE TABLE IF NOT EXISTS requests (
                    id BIGSERIAL PRIMARY KEY,
                    public_id UUID NOT NULL UNIQUE DEFAULT uuid_generate_v4(),
                    url TEXT NOT NULL,
                    headers JSONB NOT NULL,
                    body JSONB NOT NULL,
                    method TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """),
            "cron": text("""
                CREATE TABLE IF NOT EXISTS cron (
                    id BIGSERIAL PRIMARY KEY,
                    instance_id BIGINT NOT NULL,
                    interval INTEGER NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_cron_request
                        FOREIGN KEY (instance_id)
                        REFERENCES requests (id)
                        ON DELETE CASCADE
                );
            """),
            "tasks": text("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id BIGSERIAL PRIMARY KEY,
                    instance_id BIGINT NOT NULL,
                    cron_id BIGINT NOT NULL,
                    result TEXT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_tasks_request
                        FOREIGN KEY (instance_id)
                        REFERENCES requests (id)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_tasks_cron
                        FOREIGN KEY (cron_id)
                        REFERENCES cron (id)
                        ON DELETE CASCADE
                );
            """),
        }

    #Faz um loop nos comandos sql e cria as tabelas
    def _query(self) -> None:

        try:

            with self.eng.begin() as session:

                for table, sql in self.sql.items():

                    logger.info(f"Criando tabela {table} se não existir...")

                    session.execute(sql)

        except  Exception as e:

            logger.error(e)
            raise MigrationDbError(e)

    #executa todos os metodos
    def run(self) -> None:
        self._sql()
        self._query()
        self._uuid_extension()
