"""Слой downstreams: адреса соседей, HTTP-методы и JSON-контракты.

Service вызывает понятные действия, а не собирает URL и HTTP-запросы.
"""
from .http import HttpGateway


class Downstreams(HttpGateway):

    async def finish_order(self, order_id: int, status: str):
        # Callback замыкает HTTP-цепочку и при успехе, и при бизнес-отказе.
        await self._call("order", "PATCH", f"/orders/{order_id}/status", {"status": status})
