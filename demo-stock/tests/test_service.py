"""Проверки бизнес-логики без PostgreSQL и сетевых запросов."""
from dataclasses import asdict, replace
import unittest
from unittest.mock import AsyncMock
from stock_app.models.domain import ReservationData, Reservation
from stock_app.models.errors import InvalidData, RecordNotFound, DownstreamError, WorkflowError
from stock_app.service.logic import Service


class MemoryRepository:
    def __init__(self):
        self.records = {}

    async def create(self, data, status):
        record = Reservation(**asdict(data), id=len(self.records) + 1, status=status)
        self.records[record.id] = record
        return record

    async def get(self, record_id):
        return self.records.get(record_id)

    async def list(self, limit, offset):
        return list(self.records.values())[offset:offset + limit]

    async def set_status(self, record_id, status):
        record = self.records.get(record_id)
        if record is not None:
            record = replace(record, status=status)
            self.records[record_id] = record
        return record


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.repository = MemoryRepository()
        self.downstreams = AsyncMock()
        self.service = Service(self.repository, self.downstreams)

    async def test_success(self):
        result = await self.service.create(ReservationData(order_id=1, product_name="Pizza", quantity=2, amount=1000))
        self.assertEqual(result["status"], "reserved")
        self.downstreams.pay.assert_awaited_once()
        record = await self.service.get(1)
        self.assertIsInstance(record, Reservation)
        self.assertEqual(record.status, "reserved")
        self.assertEqual(await self.service.list(1, 0), [record])

    async def test_business_failure(self):
        result = await self.service.create(ReservationData(order_id=1, product_name="Pizza", quantity=6, amount=1000))
        self.assertEqual(result["status"], "rejected")
        self.downstreams.finish_order.assert_awaited_once_with(1, "failed")
        self.downstreams.pay.assert_not_awaited()

    async def test_missing_record(self):
        with self.assertRaises(RecordNotFound):
            await self.service.get(999)

    async def test_neighbor_failure_preserves_saved_record(self):
        self.downstreams.pay.side_effect = DownstreamError("Нет связи")
        with self.assertRaises(DownstreamError):
            await self.service.create(ReservationData(order_id=1, product_name="Pizza", quantity=2, amount=1000))
        self.assertEqual((await self.repository.get(1)).status, "reserved")
