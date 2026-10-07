"""Слой service: создание доставки с непустым адресом.

Здесь нет FastAPI, SQL, URL или HTTP-кодов. Зависимости передаются снаружи
через простые интерфейсы Protocol — вместо реальной БД можно дать тестовую.
"""
from .ports import RepositoryPort, DownstreamsPort
from ..models.errors import RecordNotFound
from ..models.domain import DeliveryData


class Service:
    def __init__(self, repository: RepositoryPort, downstreams: DownstreamsPort):
        self.repository = repository
        self.downstreams = downstreams

    async def create(self, data: DeliveryData):
        status = "ready" if data.address else "failed"
        record = await self.repository.create(data, status)
        if status == "ready":
            await self.downstreams.notify(data.order_id, "Order is ready")
        else:
            await self.downstreams.finish_order(data.order_id, "failed")
        return {"delivery_id": record.id, "order_id": data.order_id, "status": status}

    async def get(self, record_id: int):
        record = await self.repository.get(record_id)
        if record is None:
            raise RecordNotFound("Запись не найдена")
        return record

    async def list(self, limit: int, offset: int):
        return await self.repository.list(limit, offset)
