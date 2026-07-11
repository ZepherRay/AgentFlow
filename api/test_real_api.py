import asyncio
import sys
sys.path.insert(0, r'D:\traecn\aiskills\7.8\agentflow\api')
from app.services.llm_service import LLMService

async def main():
    # 测试真实 volcengine
    e = await LLMService.get_embedding("你好世界")
    print('volcengine dim:', len(e))
    print('first 5:', e[:5])

asyncio.run(main())
