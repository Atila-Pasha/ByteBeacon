import asyncio
import logging

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.monitor import Monitor
from app.monitoring.checker import check_monitor


logger = logging.getLogger(__name__)


class MonitorScheduler:
	def __init__(self, poll_interval: float = 5.0) -> None:
		self.poll_interval = poll_interval
		self._stop_event = asyncio.Event()
		self._supervisor_task: asyncio.Task[None] | None = None
		self._monitor_tasks: dict[int, asyncio.Task[None]] = {}
		self._monitor_signatures: dict[int, tuple[str, int]] = {}

	def start(self) -> None:
		if self._supervisor_task is not None:
			return

		self._stop_event.clear()
		self._supervisor_task = asyncio.create_task(
			self._supervise(),
			name="monitor-scheduler",
		)

	async def stop(self) -> None:
		self._stop_event.set()

		if self._supervisor_task is not None:
			await self._supervisor_task
			self._supervisor_task = None

		tasks = list(self._monitor_tasks.values())
		for task in tasks:
			task.cancel()

		if tasks:
			await asyncio.gather(*tasks, return_exceptions=True)

		self._monitor_tasks.clear()
		self._monitor_signatures.clear()

	async def _supervise(self) -> None:
		try:
			while not self._stop_event.is_set():
				await self._reconcile()

				try:
					await asyncio.wait_for(
						self._stop_event.wait(),
						timeout=self.poll_interval,
					)
				except asyncio.TimeoutError:
					continue
		except asyncio.CancelledError:
			raise
		finally:
			tasks = list(self._monitor_tasks.values())
			for task in tasks:
				task.cancel()
			if tasks:
				await asyncio.gather(*tasks, return_exceptions=True)
			self._monitor_tasks.clear()
			self._monitor_signatures.clear()

	async def _reconcile(self) -> None:
		try:
			async with AsyncSessionLocal() as db:
				result = await db.execute(
					select(Monitor).where(Monitor.is_active.is_(True))
				)
				monitors = list(result.scalars().all())
		except asyncio.CancelledError:
			raise
		except Exception:
			logger.exception("Unable to reconcile monitor tasks")
			return

		active_monitors = {monitor.id: monitor for monitor in monitors}

		for monitor_id, task in list(self._monitor_tasks.items()):
			signature = self._monitor_signatures[monitor_id]
			current_monitor = active_monitors.get(monitor_id)
			if (
				current_monitor is None
				or signature != self._signature(current_monitor)
				or task.done()
			):
				task.cancel()
				await asyncio.gather(task, return_exceptions=True)
				del self._monitor_tasks[monitor_id]
				del self._monitor_signatures[monitor_id]

		for monitor_id, monitor in active_monitors.items():
			if monitor_id in self._monitor_tasks:
				continue

			self._monitor_signatures[monitor_id] = self._signature(monitor)
			self._monitor_tasks[monitor_id] = asyncio.create_task(
				self._run_monitor(monitor),
				name=f"monitor-{monitor_id}",
			)

	@staticmethod
	def _signature(monitor: Monitor) -> tuple[str, int]:
		return monitor.url, monitor.interval

	async def _run_monitor(self, monitor: Monitor) -> None:
		while True:
			try:
				async with AsyncSessionLocal() as db:
					await check_monitor(db, monitor)
			except asyncio.CancelledError:
				raise
			except Exception:
				logger.exception(
					"Monitor check failed",
					extra={"monitor_id": monitor.id},
				)

			try:
				await asyncio.sleep(monitor.interval * 60)
			except asyncio.CancelledError:
				raise
