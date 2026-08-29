"""Executa os comandos de migração do PostgreSQL e do Redis."""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (
    "migration_db",
    "migration_redis",
)


def run_migrations() -> None:
    failures = []

    for command in COMMANDS:
        print(f"\n[EXECUTANDO] {command}", flush=True)

        result = subprocess.run(
            [sys.executable, "-m", "src.infra.manage", command],
            cwd=PROJECT_ROOT,
            check=False,
        )

        if result.returncode == 0:
            print(f"[OK] {command}", flush=True)
        else:
            failures.append(command)
            print(f"[ERRO] {command}", flush=True)

    if failures:
        failed_commands = ", ".join(failures)
        raise SystemExit(f"Migrações com erro: {failed_commands}")


if __name__ == "__main__":
    run_migrations()
