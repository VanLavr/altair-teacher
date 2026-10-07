"""Интерфейсы зависимостей service; здесь нет конкретной БД или HTTP-клиента."""
from typing import Protocol
from ..models.domain import NotificationData, Notification


class RepositoryPort(Protocol):
    async def get(self, record_id: int) -> Notification | None: ...
    async def list(self, limit: int, offset: int) -> list[Notification]: ...
    # Protocol описывает нужные операции. Service не знает о PostgreSQL.
    async def create(self, data: NotificationData, status: str) -> Notification: ...


class DownstreamsPort(Protocol):
    async def finish_order(self, order_id: int, status: str) -> None: ...
