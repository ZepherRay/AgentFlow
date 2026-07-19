from app.services.tools.base import BaseTool
from datetime import datetime


class GetCurrentTimeTool(BaseTool):
    name = "get_current_time"
    description = "获取当前系统时间"
    parameters = []

    async def execute(self, **kwargs) -> str:
        now = datetime.now()
        return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"


get_current_time = GetCurrentTimeTool()