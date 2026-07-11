import asyncio
import sys
sys.path.insert(0, r'D:\traecn\aiskills\7.8\agentflow\api')
from app.services.llm_service import LLMService, _hash_embedding

async def main():
    # 测试本地 hash embedding
    e1 = _hash_embedding("hello world")
    e2 = _hash_embedding("hello world")
    e3 = _hash_embedding("goodbye world")
    print('hash dim:', len(e1))
    print('same text same vec:', e1 == e2)
    print('different text diff vec:', e1 == e3)
    # 测试 LLM 降级
    try:
        e4 = await LLMService.get_embedding("测试中文")
        print('LLM embedding dim:', len(e4))
    except Exception as e:
        print('LLM error:', e)

asyncio.run(main())
