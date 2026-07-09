from typing import Any, Optional, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """统一返回格式"""

    code: int = 200
    message: str = "success"
    data: Optional[T] = None

    @classmethod
    def ok(cls, data: Any = None, message: str = "success") -> "ResponseModel":
        return cls(code=200, message=message, data=data)

    @classmethod
    def fail(cls, code: int = 400, message: str = "error", data: Any = None) -> "ResponseModel":
        return cls(code=code, message=message, data=data)


class PageInfo(BaseModel):
    """分页信息"""

    page: int = 1
    page_size: int = 20
    total: int = 0
    items: list = []


class PaginatedResponse(ResponseModel):
    """分页返回"""

    data: Optional[PageInfo] = None