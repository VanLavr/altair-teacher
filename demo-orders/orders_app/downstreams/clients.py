"""Слой downstreams: адреса соседей, HTTP-методы и JSON-контракты.

Service вызывает понятные действия, а не собирает URL и HTTP-запросы.
"""
from .http import HttpGateway


class Downstreams(HttpGateway):
    async def reserve(self, order_id: int, product_name: str, quantity: int, amount: int):
        await self._call("stock", "POST", "/reservations", {
            "order_id": order_id, "product_name": product_name,
            "quantity": quantity, "amount": amount,
        })
