"""Настройки из app.env рядом с makefile. Не зависят от текущего каталога.

Переменные окружения имеют приоритет над файлом. Файл читаем в словарь,
а не в глобальное окружение: настройки соседних проектов не смешиваются.
"""
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def required(values: dict, key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"В app.env нужно указать {key}")
    return value.strip()


def service_url(value: str) -> str:
    # Можно написать 192.168.1.12:8002 или полный http://192.168.1.12:8002.
    value = value.strip().rstrip("/")
    if "://" not in value:
        value = "http://" + value
    parsed = urlsplit(value)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.port is None or parsed.port == 0 or parsed.path or parsed.query or parsed.fragment
            or parsed.username or parsed.password):
        raise ValueError("Адрес сервиса должен иметь вид ip:port или http://ip:port")
    return value


@dataclass(frozen=True)
class Settings:
    database_url: str
    host: str
    port: int
    http_timeout: float
    delivery_service_url: str
    order_service_url: str
    delivery_address: str


def load_settings(path: Path | None = None, environ: dict | None = None) -> Settings:
    env_path = path if path is not None else PROJECT_ROOT / "app.env"
    # Отсутствующий файл — понятная ошибка при запуске, а не скрытый localhost.
    if not env_path.is_file():
        raise FileNotFoundError(f"Не найден файл настроек: {env_path}")
    values = dict(dotenv_values(env_path, interpolate=False))
    values.update(os.environ if environ is None else environ)
    database_url = required(values, "DATABASE_URL")
    port = int(values.get("APP_PORT", "8002"))
    timeout = float(values.get("HTTP_TIMEOUT", "30"))
    if not 1 <= port <= 65535 or not 0 < timeout < float("inf"):
        raise ValueError("APP_PORT должен быть 1..65535, HTTP_TIMEOUT — положительным числом")
    host = required(values, "APP_HOST")
    if not host:
        raise ValueError("APP_HOST не должен быть пустым")
    return Settings(
        database_url=database_url, host=host, port=port, http_timeout=timeout,
        delivery_service_url=service_url(required(values, "DELIVERY_SERVICE_URL")),
        order_service_url=service_url(required(values, "ORDER_SERVICE_URL")),
        delivery_address=values.get("DELIVERY_ADDRESS", "School"),
    )
