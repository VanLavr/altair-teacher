"""Доменные модели: данные, с которыми работает бизнес-логика.

Это обычные dataclass, без FastAPI, Pydantic, HTTP или SQL. Входной DTO
преобразуется в OrderData в controller; repository возвращает Order.
"""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class OrderData:
    product_name: str
    quantity: int
    price: int


@dataclass(frozen=True)
class Order(OrderData):
    id: int
    status: Literal["processing", "completed", "failed"]
