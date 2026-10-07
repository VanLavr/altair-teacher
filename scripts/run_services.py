"""Запуск пяти процессов Uvicorn и их остановка по Ctrl+C.

Это локальный учебный запуск, а не Docker-образ приложения. Каждый сервис
можно запустить отдельно той же командой uvicorn, как показано в README.
"""
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Внешние директории содержат дефис, поэтому внутри — обычные Python-пакеты.
# Каждый run.py запускается из собственного проекта и читает свой app.env.
SERVICES = {
    "order": ("demo-orders", "orders_app", 8000),
    "stock": ("demo-stock", "stock_app", 8001),
    "payment": ("demo-payment", "payment_app", 8002),
    "delivery": ("demo-delivery", "delivery_app", 8003),
    "notification": ("demo-notification", "notification_app", 8004),
}


def main():
    processes = []
    stopping = False

    def stop(signum, frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    exit_code = 0
    try:
        for service, (directory, package, port) in SERVICES.items():
            process = subprocess.Popen([
                sys.executable, "run.py",
            ], cwd=ROOT / directory)
            processes.append((service, process))
            print(f"{service.title()} Service: запуск из {directory}, адрес и порт — в app.env", flush=True)
        # При падении одного процесса прекращаем весь запуск: учитель сразу
        # видит ошибку, вместо частично работающей цепочки.
        while not stopping:
            for service, process in processes:
                if process.poll() is not None:
                    print(f"Процесс {service} завершился: {process.returncode}", file=sys.stderr)
                    exit_code = process.returncode or 1
                    stopping = True
                    break
            time.sleep(0.2)
    finally:
        for _, process in processes:
            if process.poll() is None:
                process.terminate()
        for _, process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
