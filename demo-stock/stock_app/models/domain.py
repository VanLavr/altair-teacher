"""Доменные модели: данные, с которыми работает бизнес-логика.

Это обычные dataclass, без FastAPI, Pydantic, HTTP или SQL. Входной DTO
преобразуется в ReservationData в controller; repository возвращает Reservation.
"""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ReservationData:
    order_id: int
    product_name: str
    quantity: int
    amount: int


@dataclass(frozen=True)
class Reservation(ReservationData):
    id: int
    status: Literal["reserved", "rejected"]
