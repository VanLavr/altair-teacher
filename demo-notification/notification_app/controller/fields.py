"""Типы полей HTTP API этого сервиса: FastAPI проверяет вход и документирует его в /docs.

Цена и сумма — целые числа в одной выбранной денежной единице (например,
рублях). Float для денег не используем. Ограничения соответствуют INTEGER
и VARCHAR в PostgreSQL. Некорректный запрос получает HTTP 422.
"""
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

PositiveInt = Annotated[int, Field(strict=True, gt=0, le=2_147_483_647)]
Money = Annotated[int, Field(strict=True, ge=0, le=2_147_483_647)]
ProductName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
Address = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]
Message = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


class Input(BaseModel):
    # Опечатка в имени поля не должна молча пропасть из запроса школьника.
    model_config = ConfigDict(extra="forbid", from_attributes=True)


