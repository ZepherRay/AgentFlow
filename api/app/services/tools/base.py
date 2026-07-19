from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod


class ToolConfig(BaseModel):
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="工具参数")


class BaseTool(ABC):
    name: str
    description: str
    parameters: List[Dict[str, Any]]

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        pass

    def to_langchain_tool(self):
        try:
            from langchain_core.tools import StructuredTool
            return StructuredTool.from_function(
                name=self.name,
                description=self.description,
                coroutine=self.execute,
            )
        except ImportError:
            from langchain.tools import AsyncStructuredTool as ToolCls
            return ToolCls.from_function(
                func=self.execute,
                name=self.name,
                description=self.description,
            )