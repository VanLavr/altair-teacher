"""Ограничения параметров HTTP-маршрутов controller."""
from typing import Annotated
from fastapi import Path, Query

RecordId = Annotated[int, Path(gt=0, le=2_147_483_647)]
Limit = Annotated[int, Query(ge=1, le=1000)]
Offset = Annotated[int, Query(ge=0)]
