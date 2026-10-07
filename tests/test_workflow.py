"""HTTP-проверки всей цепочки без локального развёртывания.

Заменяем только хранение и сеть: настоящие FastAPI-маршруты, Pydantic,
бизнес-правила и обратный PATCH работают как в пяти отдельных процессах.
Эти тесты не проверяют реальный PostgreSQL и права SQL-пользователя.
"""
from dataclasses import asdict, replace
import sys
import unittest
from unittest.mock import patch

import httpx
# Используем те же директории и пакеты, что и реальный launcher.
from scripts.run_services import ROOT, SERVICES
for directory, _, _ in SERVICES.values():
    sys.path.insert(0, str(ROOT / directory))

from orders_app import main as order
from stock_app import main as stock
from payment_app import main as payment
from delivery_app import main as delivery
from notification_app import main as notification
from orders_app.downstreams.clients import Downstreams as OrderDownstreams
from stock_app.downstreams.clients import Downstreams as StockDownstreams
from payment_app.downstreams.clients import Downstreams as PaymentDownstreams
from delivery_app.downstreams.clients import Downstreams as DeliveryDownstreams
from notification_app.downstreams.clients import Downstreams as NotificationDownstreams


class MemoryRepository:
    """Тестовый двойник repository: отдельный словарь для каждой таблицы."""
    def __init__(self, model):
        self.rows = {}
        self.model = model

    async def insert(self, **values):
        row = {"id": len(self.rows) + 1, **values}
        self.rows[row["id"]] = row
        return self.model(**row)

    async def create(self, data, status):
        return await self.insert(**asdict(data), status=status)

    async def get(self, record_id):
        row = self.rows.get(record_id)
        return self.model(**row) if row else None

    async def list(self, limit, offset):
        return [self.model(**row) for row in self.rows.values()][offset:offset + limit]

    async def set_status(self, record_id, status):
        if record_id not in self.rows:
            return None
        self.rows[record_id]["status"] = status
        return self.model(**self.rows[record_id])


class ServiceNetwork(httpx.AsyncBaseTransport):
    def __init__(self, apps):
        self.transports = {port: httpx.ASGITransport(app=app) for port, app in apps.items()}
        self.requests = []
        self.unavailable = set()

    async def handle_async_request(self, request):
        self.requests.append((request.method, request.url.port, request.url.path))
        if request.url.port in self.unavailable:
            raise httpx.ConnectError("Тест: сервис выключен", request=request)
        return await self.transports[request.url.port].handle_async_request(request)

    async def aclose(self):
        for transport in self.transports.values():
            await transport.aclose()


class WorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.apps = {8000: order.app, 8001: stock.app, 8002: payment.app,
                     8003: delivery.app, 8004: notification.app}
        self.network = ServiceNetwork(self.apps)
        self.client = httpx.AsyncClient(transport=self.network, base_url="http://127.0.0.1:8000")
        gateways = {8000: OrderDownstreams, 8001: StockDownstreams, 8002: PaymentDownstreams,
                    8003: DeliveryDownstreams, 8004: NotificationDownstreams}
        self.original_states = {}
        for port, app in self.apps.items():
            self.original_states[port] = dict(app.state._state)
            app.state.repository = MemoryRepository(app.state.repository.model)
            addresses = {name: f"http://127.0.0.1:{service_port}" for name, service_port in
                         [("order_service_url", 8000), ("stock_service_url", 8001),
                          ("payment_service_url", 8002), ("delivery_service_url", 8003),
                          ("notification_service_url", 8004)] if hasattr(app.state.settings, name)}
            settings = replace(app.state.settings, **addresses)
            app.state.downstreams = gateways[port](self.client, settings)
        payment.app.state.delivery_address = "School"

    async def asyncTearDown(self):
        await self.client.aclose()
        for port, app in self.apps.items():
            app.state._state.clear()
            app.state._state.update(self.original_states[port])

    async def create(self, **changes):
        payload = {"product_name": "Pizza", "quantity": 2, "price": 500, **changes}
        return await self.client.post("/orders", json=payload)

    async def records(self, port, resource):
        response = await self.client.get(f"http://127.0.0.1:{port}/{resource}")
        self.assertEqual(response.status_code, 200)
        return response.json()

    async def test_success_whole_chain_and_get_routes(self):
        response = await self.create()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "completed")
        self.assertEqual(self.network.requests[:6], [
            ("POST", 8000, "/orders"), ("POST", 8001, "/reservations"),
            ("POST", 8002, "/payments"), ("POST", 8003, "/deliveries"),
            ("POST", 8004, "/notifications"), ("PATCH", 8000, "/orders/1/status"),
        ])
        for port, resource, status in [(8000, "orders", "completed"), (8001, "reservations", "reserved"),
                                      (8002, "payments", "paid"), (8003, "deliveries", "ready"),
                                      (8004, "notifications", "sent")]:
            rows = await self.records(port, resource)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["status"], status)
            item = await self.client.get(f"http://127.0.0.1:{port}/{resource}/1")
            self.assertEqual(item.json(), rows[0])
            missing = await self.client.get(f"http://127.0.0.1:{port}/{resource}/999")
            self.assertEqual(missing.status_code, 404)
        self.assertEqual((await self.records(8001, "reservations"))[0]["amount"], 1000)
        self.assertEqual((await self.records(8003, "deliveries"))[0]["address"], "School")

    async def test_stock_rejection_stops_payment_and_finishes_order(self):
        response = await self.create(quantity=6)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "failed")
        self.assertEqual((await self.records(8001, "reservations"))[0]["status"], "rejected")
        self.assertEqual(await self.records(8002, "payments"), [])

    async def test_payment_rejection_stops_delivery_and_finishes_order(self):
        response = await self.create(quantity=1, price=5001)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "failed")
        self.assertEqual((await self.records(8002, "payments"))[0]["status"], "failed")
        self.assertEqual(await self.records(8003, "deliveries"), [])

    async def test_inclusive_business_boundaries(self):
        response = await self.create(quantity=5, price=1000)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "completed")

    async def test_empty_delivery_address_stops_notifications(self):
        with patch.object(payment.app.state, "delivery_address", "   "):
            response = await self.create()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "failed")
        self.assertEqual((await self.records(8003, "deliveries"))[0]["status"], "failed")
        self.assertEqual(await self.records(8004, "notifications"), [])

    async def test_empty_notification_sets_order_failed(self):
        await order.app.state.repository.insert(product_name="Pizza", quantity=1, price=500, status="processing")
        response = await self.client.post("http://127.0.0.1:8004/notifications", json={"order_id": 1, "message": " "})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "failed")
        self.assertEqual((await self.client.get("/orders/1")).json()["status"], "failed")

    async def test_unavailable_service_preserves_partial_results_and_order_id(self):
        self.network.unavailable.add(8003)
        response = await self.create()
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"]["order_id"], 1)
        self.assertEqual((await self.client.get("/orders/1")).json()["status"], "failed")
        self.assertEqual((await self.records(8002, "payments"))[0]["status"], "paid")
        self.assertEqual(await self.records(8004, "notifications"), [])

    async def test_unavailable_callback_does_not_return_success(self):
        self.network.unavailable.add(8000)
        # Отправляем внешний запрос напрямую через ASGI, минуя имитацию сбоя
        # входящего соединения. Сбой будет на обратном PATCH уведомления.
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=order.app), base_url="http://test") as ui:
            response = await ui.post("/orders", json={"product_name": "Pizza", "quantity": 1, "price": 100})
        self.assertEqual(response.status_code, 502)
        self.assertEqual((await order.app.state.repository.get(1)).status, "failed")
        self.assertEqual((await self.records(8004, "notifications"))[0]["status"], "sent")

    async def test_input_validation_and_amount_overflow(self):
        for changes in [{"quantity": 0}, {"price": -1}, {"quantity": 1.5}, {"quantity": True},
                        {"product_name": " "}, {"product_name": "a" * 256}, {"prcie": 100},
                        {"quantity": 2, "price": 2_147_483_647}]:
            with self.subTest(changes=changes):
                response = await self.create(**changes)
                self.assertEqual(response.status_code, 422)
        self.assertEqual(await self.records(8000, "orders"), [])

    async def test_patch_validation_missing_order_and_pagination(self):
        missing = await self.client.patch("/orders/999/status", json={"status": "completed"})
        self.assertEqual(missing.status_code, 404)
        invalid = await self.client.patch("/orders/1/status", json={"status": "unknown"})
        self.assertEqual(invalid.status_code, 422)
        await self.create()
        await self.create()
        response = await self.client.get("/orders?limit=1&offset=1")
        self.assertEqual([row["id"] for row in response.json()], [2])
        self.assertEqual((await self.client.get("/orders?limit=0")).status_code, 422)
        self.assertEqual((await self.client.get("/orders/0")).status_code, 422)

    async def test_health_and_openapi(self):
        for port in self.apps:
            health = await self.client.get(f"http://127.0.0.1:{port}/health")
            self.assertEqual(health.status_code, 200)
            response = await self.client.get(f"http://127.0.0.1:{port}/openapi.json")
            self.assertEqual(response.status_code, 200)
            self.assertIn("paths", response.json())
