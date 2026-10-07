"""Модели данных этого сервиса: проверка запросов и описание ответов.

Это HTTP DTO. Бизнес-слой работает с отдельными dataclass из models/domain.py.
"""
from typing import Literal
from pydantic import BaseModel
from .fields import Input, PositiveInt, Money, ProductName


class ReservationCreate(Input):
    order_id: PositiveInt
    product_name: ProductName
    quantity: PositiveInt
    amount: Money


class ReservationRead(ReservationCreate):
    id: int
    status: Literal["reserved", "rejected"]


class ReservationResult(BaseModel):
    reservation_id: int
    order_id: int
    status: Literal["reserved", "rejected"]
