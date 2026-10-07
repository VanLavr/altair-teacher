"""Слой service: уведомление и завершение обработки заказа.

Здесь нет FastAPI, SQL, URL или HTTP-кодов. Зависимости передаются снаружи
через простые интерфейсы Protocol — вместо реальной БД можно дать тестовую.
"""
from .ports import RepositoryPort, DownstreamsPort
from ..models.errors import RecordNotFound
from ..models.domain import NotificationData


class Service:
    def __init__(self, repository: RepositoryPort, downstreams: DownstreamsPort):
        self.repository = repository
        self.downstreams = downstreams

    async def create(self, data: NotificationData):
        status = "sent" if data.message else "failed"
        # sent — имитация отправки. Настоящих SMS/email здесь нет.
        record = await self.repository.create(data, status)
        await self.downstreams.finish_order(data.order_id, "completed" if status == "sent" else "failed")
        return {"notification_id": record.id, "order_id": data.order_id, "status": status}

    async def get(self, record_id: int):
        record = await self.repository.get(record_id)
        if record is None:
            raise RecordNotFound("Запись не найдена")
        return record

    async def list(self, limit: int, offset: int):
        return await self.repository.list(limit, offset)
