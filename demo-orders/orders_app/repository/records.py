"""Слой repository: только SQL и таблица orders.

Решение о статусе принимает service; repository сохраняет готовые данные.
"""
from psycopg import sql
from .postgres import PostgresRepository
from dataclasses import asdict
from ..models.domain import OrderData


class Repository(PostgresRepository):
    def __init__(self, database_url: str):
        # Все приложения получают один URL, но каждое работает со своей таблицей.
        super().__init__(database_url, "orders")

    async def create(self, data: OrderData, status: str):
        return await self._insert(**asdict(data), status=status)

    async def set_status(self, record_id: int, status: str):
        # Изменяет только таблицу orders. Возвращает None, если заказа нет.
        return await self._query(
            sql.SQL("UPDATE orders SET status = %s WHERE id = %s RETURNING *"),
            (status, record_id),
        )
