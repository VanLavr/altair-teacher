"""Слой controller: принимает HTTP, проверяет модели и вызывает service.

Depends просит FastAPI передать Service в обработчик. Контроллер не выполняет
SQL и не вызывает соседей. Он только переводит HTTP-запрос в действие.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Request
from .parameters import RecordId, Limit, Offset
from .schemas import ReservationCreate, ReservationRead, ReservationResult
from ..service.logic import Service
from ..models.domain import ReservationData

router = APIRouter()


async def get_service(request: Request) -> Service:
    # Берём зависимости из main.py. В тестах здесь будут тестовые адаптеры.
    return Service(request.app.state.repository, request.app.state.downstreams)


ServiceDependency = Annotated[Service, Depends(get_service)]


@router.post("/reservations", response_model=ReservationResult, status_code=201)
async def create(data: ReservationCreate, service: ServiceDependency):
    return await service.create(ReservationData(**data.model_dump()))


@router.get("/reservations", response_model=list[ReservationRead])
async def list_records(service: ServiceDependency, limit: Limit = 100, offset: Offset = 0):
    return await service.list(limit, offset)


@router.get("/reservations/{record_id}", response_model=ReservationRead)
async def get_record(record_id: RecordId, service: ServiceDependency):
    return await service.get(record_id)


@router.get("/health", tags=["Диагностика"])
async def health(service: ServiceDependency):
    await service.list(1, 0)
    return {"service": "stock", "status": "ok"}
