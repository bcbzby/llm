from pydantic import BaseModel
from typing import Any


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: Any = None
    request_id: str | None = None
