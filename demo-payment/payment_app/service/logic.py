"""Слой service: условная оплата суммы до 5000 включительно.

Здесь нет FastAPI, SQL, URL или HTTP-кодов. Зависимости передаются снаружи
через простые интерфейсы Protocol — вместо реальной БД можно дать тестовую.
"""
from .ports import RepositoryPort, DownstreamsPort
from ..models.errors import RecordNotFound
from ..models.domain import PaymentData


class Service:
    def __init__(self, repository: RepositoryPort, downstreams: DownstreamsPort, address: str = "School"):
        self.repository = repository
        self.downstreams = downstreams
        self.address = address

    async def create(self, data: PaymentData):
        status = "paid" if data.amount <= 5000 else "failed"
        record = await self.repository.create(data, status)
        if status == "paid":
            # В контракте оплаты адреса нет: передаём учебный адрес из настроек.
            await self.downstreams.deliver(data.order_id, self.address)
        else:
            await self.downstreams.finish_order(data.order_id, "failed")
        return {"payment_id": record.id, "order_id": data.order_id, "status": status}

    async def get(self, record_id: int):
        record = await self.repository.get(record_id)
        if record is None:
            raise RecordNotFound("Запись не найдена")
        return record

    async def list(self, limit: int, offset: int):
        return await self.repository.list(limit, offset)
