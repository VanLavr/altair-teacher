"""Слой service: создание заказа и получение итогового статуса.

Здесь нет FastAPI, SQL, URL или HTTP-кодов. Зависимости передаются снаружи
через простые интерфейсы Protocol — вместо реальной БД можно дать тестовую.
"""
from .ports import RepositoryPort, DownstreamsPort
from ..models.errors import DownstreamError, WorkflowError, InvalidData, RecordNotFound
from ..models.domain import OrderData


class Service:
    def __init__(self, repository: RepositoryPort, downstreams: DownstreamsPort):
        self.repository = repository
        self.downstreams = downstreams

    async def create(self, data: OrderData):
        amount = data.quantity * data.price
        if amount > 2_147_483_647:
            raise InvalidData("Сумма quantity * price превышает диапазон INTEGER")
        # Сначала COMMIT заказа, затем HTTP: callback увидит готовую запись.
        order = await self.repository.create(data, "processing")
        try:
            await self.downstreams.reserve(order.id, data.product_name, data.quantity, amount)
        except DownstreamError as exc:
            await self.repository.set_status(order.id, "failed")
            # Контроллер вернёт ID уже сохранённого заказа вместе с ошибкой.
            raise WorkflowError(order.id, str(exc)) from exc
        # Обратный PATCH уже изменил запись: читаем актуальный статус.
        return await self.get(order.id)

    async def update_status(self, record_id: int, status: str):
        order = await self.repository.set_status(record_id, status)
        if order is None:
            raise RecordNotFound("Заказ не найден")
        return {"id": order.id, "status": order.status}

    async def get(self, record_id: int):
        record = await self.repository.get(record_id)
        if record is None:
            raise RecordNotFound("Запись не найдена")
        return record

    async def list(self, limit: int, offset: int):
        return await self.repository.list(limit, offset)
