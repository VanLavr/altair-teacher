"""Модели данных этого сервиса: проверка запросов и описание ответов.

Это HTTP DTO. Бизнес-слой работает с отдельными dataclass из models/domain.py.
"""
from typing import Literal
from pydantic import BaseModel
from .fields import Input, PositiveInt, Address


class DeliveryCreate(Input):
    order_id: PositiveInt
    # Пустая строка допустима: это бизнес-отказ failed, а не ошибка формата.
    address: Address


class DeliveryRead(DeliveryCreate):
    id: int
    status: Literal["ready", "failed"]


class DeliveryResult(BaseModel):
    delivery_id: int
    order_id: int
    status: Literal["ready", "failed"]
