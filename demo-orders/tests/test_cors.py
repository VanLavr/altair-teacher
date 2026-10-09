"""HTML-файл должен иметь доступ к API через браузерный CORS."""
from dataclasses import replace
import unittest
from unittest.mock import AsyncMock
import httpx
from orders_app.config import load_settings
from orders_app.main import create_app


class CorsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.settings = load_settings(environ={})
        self.app = create_app(replace(self.settings, cors_origins=("null",)))
        self.app.state.repository = AsyncMock()
        self.app.state.repository.list.return_value = []
        # Список не вызывает соседей, но controller получает эту зависимость.
        self.app.state.downstreams = AsyncMock()
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_file_get(self):
        response = await self.client.get("/orders", headers={"Origin": "null"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        self.assertEqual(response.headers["access-control-allow-origin"], "null")

    async def test_json_post_preflight(self):
        response = await self.client.options("/orders", headers={
            "Origin": "null", "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "null")
        self.assertIn("POST", response.headers["access-control-allow-methods"])

    async def test_validation_error_is_readable_by_browser(self):
        response = await self.client.post("/orders", headers={"Origin": "null"}, json={"quantity": 0})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.headers["access-control-allow-origin"], "null")

    async def test_unconfigured_origin(self):
        response = await self.client.options("/orders", headers={
            "Origin": "http://unconfigured.example", "Access-Control-Request-Method": "POST",
        })
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("access-control-allow-origin", response.headers)
