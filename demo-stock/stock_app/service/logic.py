"""Слой service: резервирование не более пяти единиц товара.

Здесь нет FastAPI, SQL, URL или HTTP-кодов. Зависимости передаются снаружи
через простые интерфейсы Protocol — вместо реальной БД можно дать тестовую.
"""
from .ports import RepositoryPort, DownstreamsPort
from ..models.errors import RecordNotFound
from ..models.domain import ReservationData


class Service:
    def __init__(self, repository: RepositoryPort, downstreams: DownstreamsPort):
        self.repository = repository
        self.downstreams = downstreams

    async def create(self, data: ReservationData):
        status = "reserved" if data.quantity <= 5 else "rejected"
        record = await self.repository.create(data, status)
        if status == "reserved":
            await self.downstreams.pay(data.order_id, data.amount)
        else:
            await self.downstreams.finish_order(data.order_id, "failed")
        return {"reservation_id": record.id, "order_id": data.order_id, "status": status}

    async def get(self, record_id: int):
        record = await self.repository.get(record_id)
        if record is None:
            raise RecordNotFound("Запись не найдена")
        return record

    async def list(self, limit: int, offset: int):
        return await self.repository.list(limit, offset)
