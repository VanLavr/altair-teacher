"""Доменные модели: данные, с которыми работает бизнес-логика.

Это обычные dataclass, без FastAPI, Pydantic, HTTP или SQL. Входной DTO
преобразуется в PaymentData в controller; repository возвращает Payment.
"""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PaymentData:
    order_id: int
    amount: int


@dataclass(frozen=True)
class Payment(PaymentData):
    id: int
    status: Literal["paid", "failed"]
