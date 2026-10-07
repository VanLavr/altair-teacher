"""Проверки бизнес-логики без PostgreSQL и сетевых запросов."""
from dataclasses import asdict, replace
import unittest
from unittest.mock import AsyncMock
from orders_app.models.domain import OrderData, Order
from orders_app.models.errors import InvalidData, RecordNotFound, DownstreamError, WorkflowError
from orders_app.service.logic import Service


class MemoryRepository:
    def __init__(self):
        self.records = {}

    async def create(self, data, status):
        record = Order(**asdict(data), id=len(self.records) + 1, status=status)
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

        # Имитация финального callback: HTTP-сеть для теста не нужна.
        async def complete(order_id, product_name, quantity, amount):
            await self.repository.set_status(order_id, "completed")
        self.downstreams.reserve.side_effect = complete

    async def test_success(self):
        result = await self.service.create(OrderData(product_name="Pizza", quantity=2, price=500))
        self.assertIsInstance(result, Order)
        self.assertEqual(result.status, "completed")
        self.downstreams.reserve.assert_awaited_once()
        record = await self.service.get(1)
        self.assertIsInstance(record, Order)
        self.assertEqual(record.status, "completed")
        self.assertEqual(await self.service.list(1, 0), [record])

    async def test_business_failure(self):
        with self.assertRaises(InvalidData):
            await self.service.create(OrderData(product_name="Pizza", quantity=2, price=2_147_483_647))
        self.assertEqual(self.repository.records, {})
        self.downstreams.reserve.assert_not_awaited()

    async def test_missing_record(self):
        with self.assertRaises(RecordNotFound):
            await self.service.get(999)

    async def test_neighbor_failure_preserves_saved_record(self):
        self.downstreams.reserve.side_effect = DownstreamError("Нет связи")
        with self.assertRaises(WorkflowError) as error:
            await self.service.create(OrderData(product_name="Pizza", quantity=2, price=500))
        self.assertEqual(error.exception.order_id, 1)
        self.assertEqual((await self.repository.get(1)).status, "failed")
