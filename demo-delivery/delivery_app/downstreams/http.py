"""HTTP-транспорт этого сервиса. Адреса берутся только из его конфигурации."""
import logging
import httpx
from ..config import Settings
from ..models.errors import DownstreamError

logger = logging.getLogger("uvicorn.error")


class HttpGateway:
    def __init__(self, client: httpx.AsyncClient, settings: Settings):
        self.client = client
        self.settings = settings

    async def _call(self, service: str, method: str, path: str, payload: dict):
        base_url = getattr(self.settings, f"{service}_service_url")
        try:
            response = await self.client.request(method, base_url + path, json=payload)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Сервис %s не смог обработать %s: %s", service, path, exc)
            raise DownstreamError(f"Не удалось выполнить запрос к {service} service") from exc
