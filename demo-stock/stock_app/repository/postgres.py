"""SQL-механизм repository сервиса: таблица reservations в orders_db.

Этот код принадлежит данному репозиторию; другие проекты не импортируются.
"""
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from ..models.domain import Reservation


class PostgresRepository:
    def __init__(self, database_url: str, table: str):
        self.database_url = database_url
        self.table = table
        self.model = Reservation

    async def _query(self, query, parameters=(), *, many=False):
        # Отдельное короткое соединение делает пример проще пула соединений.
        # Контекстный менеджер делает COMMIT при успехе и ROLLBACK при ошибке.
        # До HTTP-вызова следующего сервиса соединение уже закрыто: иначе
        # обратный PATCH мог бы ждать блокировку незавершённого INSERT заказа.
        async with await psycopg.AsyncConnection.connect(
            self.database_url, row_factory=dict_row, connect_timeout=5
        ) as connection:
            cursor = await connection.execute(query, parameters)
            if many:
                rows = await cursor.fetchall()
                return [self.model(**row) for row in rows]
            row = await cursor.fetchone()
            return self.model(**row) if row is not None else None

    async def _insert(self, **values):
        # SQL.Identifier экранирует имена, а %s передаёт значения отдельно
        # от SQL. Никогда не подставляем пользовательский текст через f-string.
        query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
            sql.Identifier(self.table),
            sql.SQL(", ").join(map(sql.Identifier, values)),
            sql.SQL(", ").join(sql.Placeholder() for _ in values),
        )
        return await self._query(query, tuple(values.values()))

    async def get(self, record_id: int):
        return await self._query(
            sql.SQL("SELECT * FROM {} WHERE id = %s").format(sql.Identifier(self.table)),
            (record_id,),
        )

    async def list(self, limit: int, offset: int):
        return await self._query(
            sql.SQL("SELECT * FROM {} ORDER BY id LIMIT %s OFFSET %s").format(
                sql.Identifier(self.table)
            ), (limit, offset), many=True,
        )

