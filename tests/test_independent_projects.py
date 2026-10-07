"""Каждый проект должен работать после копирования без соседних директорий."""
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from scripts.run_services import ROOT, SERVICES


class IndependentProjectTests(unittest.TestCase):
    def test_projects_in_isolation(self):
        # -I убирает PYTHONPATH и путь исходного репозитория. В subprocess
        # добавляется только копия одного сервиса; установленными остаются
        # обычные сторонние зависимости FastAPI/httpx/psycopg/python-dotenv.
        code = '''
import asyncio
import importlib
import sys
from pathlib import Path
from unittest.mock import AsyncMock
import httpx

project = Path.cwd()
sys.path.insert(0, str(project))
module = importlib.import_module(sys.argv[1] + ".main")
settings = module.load_settings(environ={})
assert settings.host == "0.0.0.0"
assert module.load_settings.__module__.startswith(sys.argv[1] + ".")
app = module.create_app(settings)
app.state.repository = AsyncMock()
app.state.repository.list.return_value = []

async def check():
    # Запускаем только lifecycle приложения в памяти, без сервера и сокетов.
    async with app.router.lifespan_context(app):
        assert app.state.downstreams.settings == settings
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200, response.text
            response = await client.get("/openapi.json")
            assert response.status_code == 200
            assert sys.argv[2] in response.json()["paths"]

asyncio.run(check())
'''
        with TemporaryDirectory() as temp:
            for directory, package, _ in SERVICES.values():
                with self.subTest(project=directory):
                    copy = Path(temp) / directory
                    shutil.copytree(ROOT / directory, copy,
                                    ignore=shutil.ignore_patterns(".venv", "__pycache__", ".git"))
                    # Файл доступен и после переноса, пути вычисляются от config.py.
                    module_name = package.replace("_app", "")
                    resource = {"orders": "orders", "stock": "reservations", "payment": "payments",
                                "delivery": "deliveries", "notification": "notifications"}[module_name]
                    result = subprocess.run(
                        [sys.executable, "-I", "-c", code, package, "/" + resource],
                        cwd=copy, capture_output=True, text=True, timeout=30,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
