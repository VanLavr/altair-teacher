"""Модели данных этого сервиса: проверка запросов и описание ответов.

Это HTTP DTO. Бизнес-слой работает с отдельными dataclass из models/domain.py.
"""
from typing import Literal
from pydantic import BaseModel
from .fields import Input, PositiveInt, Money


class PaymentCreate(Input):
    order_id: PositiveInt
    amount: Money


class PaymentRead(PaymentCreate):
    id: int
    status: Literal["paid", "failed"]


class PaymentResult(BaseModel):
    payment_id: int
    order_id: int
    status: Literal["paid", "failed"]
