"""Модели данных этого сервиса: проверка запросов и описание ответов.

Это HTTP DTO. Бизнес-слой работает с отдельными dataclass из models/domain.py.
"""
from typing import Literal
from pydantic import BaseModel
from .fields import Input, PositiveInt, Money, ProductName


class OrderCreate(Input):
    product_name: ProductName
    quantity: PositiveInt
    price: Money


class OrderRead(OrderCreate):
    id: int
    status: Literal["processing", "completed", "failed"]


class OrderStatus(Input):
    status: Literal["completed", "failed"]


class OrderStatusResult(OrderStatus):
    id: int
