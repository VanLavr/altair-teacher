"""Слой controller: принимает HTTP, проверяет модели и вызывает service.

Depends просит FastAPI передать Service в обработчик. Контроллер не выполняет
SQL и не вызывает соседей. Он только переводит HTTP-запрос в действие.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Request
from .parameters import RecordId, Limit, Offset
from .schemas import NotificationCreate, NotificationRead, NotificationResult
from ..service.logic import Service
from ..models.domain import NotificationData

router = APIRouter()


async def get_service(request: Request) -> Service:
    # Берём зависимости из main.py. В тестах здесь будут тестовые адаптеры.
    return Service(request.app.state.repository, request.app.state.downstreams)


ServiceDependency = Annotated[Service, Depends(get_service)]


@router.post("/notifications", response_model=NotificationResult, status_code=201)
async def create(data: NotificationCreate, service: ServiceDependency):
    return await service.create(NotificationData(**data.model_dump()))


@router.get("/notifications", response_model=list[NotificationRead])
async def list_records(service: ServiceDependency, limit: Limit = 100, offset: Offset = 0):
    return await service.list(limit, offset)


@router.get("/notifications/{record_id}", response_model=NotificationRead)
async def get_record(record_id: RecordId, service: ServiceDependency):
    return await service.get(record_id)


@router.get("/health", tags=["Диагностика"])
async def health(service: ServiceDependency):
    await service.list(1, 0)
    return {"service": "notification", "status": "ok"}
