"""Проверяем app.env и адреса соседей, не подключаясь к сети."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from orders_app.config import load_settings, service_url


class ConfigTests(unittest.TestCase):
    def test_file_and_environment_override(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "app.env"
            path.write_text('DATABASE_URL=postgresql://orders:1234@192.168.1.10:5433/orders_db\nAPP_HOST=0.0.0.0\nAPP_PORT=8000\nSTOCK_SERVICE_URL=192.168.1.11:8001\n')
            settings = load_settings(path, environ={"APP_PORT": "9000"})
        self.assertEqual(settings.host, "0.0.0.0")
        self.assertEqual(settings.port, 9000)
        self.assertEqual(settings.stock_service_url, "http://192.168.1.11:8001")
        self.assertEqual(settings.database_url, "postgresql://orders:1234@192.168.1.10:5433/orders_db")

    def test_invalid_addresses(self):
        for value in ["", "localhost", "localhost:0", "localhost:70000", "ftp://localhost:80", "localhost:80/path"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                service_url(value)
        self.assertEqual(service_url("http://192.168.1.10:8000/"), "http://192.168.1.10:8000")

    def test_missing_database(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "app.env"
            path.write_text("APP_PORT=8000\n")
            with self.assertRaisesRegex(ValueError, "DATABASE_URL"):
                load_settings(path, environ={})
