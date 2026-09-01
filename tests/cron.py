"""Testes da lógica do loop de agendamento."""

import asyncio
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent

sys.path = [
    path
    for path in sys.path
    if Path(path or ".").resolve() != TESTS_DIR
]
sys.path.insert(0, str(PROJECT_ROOT))

from src.aplication.cron import manage as cron_manage


class TestCronLoop(unittest.IsolatedAsyncioTestCase):

    async def _run_one_iteration(
        self,
        schedule: list[tuple[str, float]],
        instance: dict | None,
    ) -> tuple[AsyncMock, object]:
        sorted_get = AsyncMock(
            side_effect=[schedule, asyncio.CancelledError()]
        )
        select = AsyncMock(return_value=instance)

        with (
            patch.object(cron_manage.client, "sorted_get", new=sorted_get),
            patch.object(
                cron_manage.control_db.requests,
                "select",
                new=select,
            ),
            patch.object(cron_manage.execute_task, "delay") as delay,
        ):
            with self.assertRaises(asyncio.CancelledError):
                await cron_manage.cron_loop()

        return select, delay

    async def test_dispatches_task_when_schedule_is_due(self) -> None:
        instance = {
            "id": 10,
            "created_at": (
                datetime.now(timezone.utc) - timedelta(days=2)
            ).isoformat(),
        }

        select, delay = await self._run_one_iteration(
            schedule=[("10", 1.0)],
            instance=instance,
        )

        select.assert_awaited_once_with(search="id", value="10")
        delay.assert_called_once_with(instance)

    async def test_does_not_dispatch_task_before_next_run(self) -> None:
        instance = {
            "id": 10,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        select, delay = await self._run_one_iteration(
            schedule=[("10", 1.0)],
            instance=instance,
        )

        select.assert_awaited_once_with(search="id", value="10")
        delay.assert_not_called()

    async def test_ignores_schedule_without_request(self) -> None:
        select, delay = await self._run_one_iteration(
            schedule=[("999", 1.0)],
            instance=None,
        )

        select.assert_awaited_once_with(search="id", value="999")
        delay.assert_not_called()


if __name__ == "__main__":
    unittest.main()
