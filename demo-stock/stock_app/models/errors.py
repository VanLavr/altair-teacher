"""Ошибки приложения без привязки к HTTP. HTTP-коды выбирает внешний слой."""


class RecordNotFound(Exception):
    pass


class InvalidData(Exception):
    pass


class DownstreamError(Exception):
    """Соседний сервис недоступен или вернул ошибку."""


class WorkflowError(DownstreamError):
    def __init__(self, order_id: int, message: str):
        super().__init__(message)
        self.order_id = order_id
