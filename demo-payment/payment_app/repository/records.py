"""Слой repository: только SQL и таблица payments.

Решение о статусе принимает service; repository сохраняет готовые данные.
"""
from .postgres import PostgresRepository
from dataclasses import asdict
from ..models.domain import PaymentData


class Repository(PostgresRepository):
    def __init__(self, database_url: str):
        # Все приложения получают один URL, но каждое работает со своей таблицей.
        super().__init__(database_url, "payments")

    async def create(self, data: PaymentData, status: str):
        return await self._insert(**asdict(data), status=status)
