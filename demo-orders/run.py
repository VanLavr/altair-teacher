"""Запуск только этого сервиса: python run.py. Настройки находятся в app.env."""
import uvicorn
from orders_app.config import load_settings


if __name__ == "__main__":
    settings = load_settings()
    # 0.0.0.0 — адрес прослушивания. В браузере используют IP компьютера.
    uvicorn.run("orders_app.main:app", host=settings.host, port=settings.port)
