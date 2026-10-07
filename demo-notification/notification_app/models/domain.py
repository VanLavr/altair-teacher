"""Доменные модели: данные, с которыми работает бизнес-логика.

Это обычные dataclass, без FastAPI, Pydantic, HTTP или SQL. Входной DTO
преобразуется в NotificationData в controller; repository возвращает Notification.
"""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class NotificationData:
    order_id: int
    message: str


@dataclass(frozen=True)
class Notification(NotificationData):
    id: int
    status: Literal["sent", "failed"]
