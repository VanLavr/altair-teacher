"""Слой controller: принимает HTTP, проверяет модели и вызывает service.

Depends просит FastAPI передать Service в обработчик. Контроллер не выполняет
SQL и не вызывает соседей. Он только переводит HTTP-запрос в действие.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Request
from .parameters import RecordId, Limit, Offset
from .schemas import PaymentCreate, PaymentRead, PaymentResult
from ..service.logic import Service
from ..models.domain import PaymentData

router = APIRouter()


async def get_service(request: Request) -> Service:
    # Берём зависимости из main.py. В тестах здесь будут тестовые адаптеры.
    return Service(request.app.state.repository, request.app.state.downstreams, request.app.state.delivery_address)


ServiceDependency = Annotated[Service, Depends(get_service)]


@router.post("/payments", response_model=PaymentResult, status_code=201)
async def create(data: PaymentCreate, service: ServiceDependency):
    return await service.create(PaymentData(**data.model_dump()))


@router.get("/payments", response_model=list[PaymentRead])
async def list_records(service: ServiceDependency, limit: Limit = 100, offset: Offset = 0):
    return await service.list(limit, offset)


@router.get("/payments/{record_id}", response_model=PaymentRead)
async def get_record(record_id: RecordId, service: ServiceDependency):
    return await service.get(record_id)


@router.get("/health", tags=["Диагностика"])
async def health(service: ServiceDependency):
    await service.list(1, 0)
    return {"service": "payment", "status": "ok"}
