import toml
from urllib.parse import quote_plus
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """全局配置，从 settings.toml 加载"""

    # App
    APP_NAME: str = "AgentFlow"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "root@123"
    DB_NAME: str = "agentflow"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_DECODE_RESPONSES: bool = True

    # OSS
    OSS_PROVIDER: str = "aliyun"
    OSS_ENDPOINT: str = ""
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET_NAME: str = ""
    OSS_REGION: str = ""

    # LLM
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    LLM_MAX_TOKENS: int = 2048
    LLM_TEMPERATURE: float = 0.7

    # Vector Store
    VECTOR_STORE_TYPE: str = "faiss"
    VECTOR_FAISS_INDEX_PATH: str = "./data/faiss_index"
    VECTOR_DIMENSION: int = 1536

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{quote_plus(self.DB_PASSWORD)}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    class Config:
        env_prefix = "AF_"


def load_settings() -> Settings:
    """从 settings.toml 加载配置并覆盖到 Settings"""
    s = Settings()
    config_path = Path(__file__).parent / "settings.toml"
    if config_path.exists():
        data = toml.load(config_path)
        for section, values in data.items():
            for key, value in values.items():
                env_key = f"{section.upper()}_{key.upper()}"
                if hasattr(s, env_key):
                    setattr(s, env_key, value)
    return s


settings = load_settings()