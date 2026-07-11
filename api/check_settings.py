import os
import sys
sys.path.insert(0, r'D:\traecn\aiskills\7.8\agentflow\api')
os.chdir(r'D:\traecn\aiskills\7.8\agentflow\api')
from dotenv import load_dotenv
load_dotenv(r'D:\traecn\aiskills\7.8\agentflow\api\.env', override=True)
from pydantic_settings import BaseSettings, SettingsConfigDict

class S(BaseSettings):
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = ""
    model_config = SettingsConfigDict(
        env_file=r'D:\traecn\aiskills\7.8\agentflow\api\.env',
        env_file_encoding="utf-8",
        extra="ignore",
    )

s = S()
print('KEY:', s.LLM_API_KEY[:20] if s.LLM_API_KEY else 'EMPTY')
print('BASE:', s.LLM_API_BASE)
