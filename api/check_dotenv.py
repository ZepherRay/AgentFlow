from dotenv import load_dotenv
import os
load_dotenv(r'D:\traecn\aiskills\7.8\agentflow\api\.env', override=True)
print('LLM_API_KEY from os:', os.getenv('LLM_API_KEY', 'EMPTY')[:30])
