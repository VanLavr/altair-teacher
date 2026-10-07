"""Доменные модели: данные, с которыми работает бизнес-логика.

Это обычные dataclass, без FastAPI, Pydantic, HTTP или SQL. Входной DTO
преобразуется в DeliveryData в controller; repository возвращает Delivery.
"""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class DeliveryData:
    order_id: int
    address: str


@dataclass(frozen=True)
class Delivery(DeliveryData):
    id: int
    status: Literal["ready", "failed"]
