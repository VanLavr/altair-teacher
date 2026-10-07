"""Модели данных этого сервиса: проверка запросов и описание ответов.

Это HTTP DTO. Бизнес-слой работает с отдельными dataclass из models/domain.py.
"""
from typing import Literal
from pydantic import BaseModel
from .fields import Input, PositiveInt, Message


class NotificationCreate(Input):
    order_id: PositiveInt
    message: Message


class NotificationRead(NotificationCreate):
    id: int
    status: Literal["sent", "failed"]


class NotificationResult(BaseModel):
    notification_id: int
    order_id: int
    status: Literal["sent", "failed"]
