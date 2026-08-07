import toml
from urllib.parse import quote_plus
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# 显式加载 .env 到环境变量（必须在 Settings 之前）
_ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=str(_ENV_PATH), override=True)


class Settings(BaseSettings):
    """全局配置，从 settings.toml 和环境变量加载"""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # App
    APP_NAME: str = "AgentFlow"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

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
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Tencent Hunyuan
    HUNYUAN_API_KEY: str = ""
    HUNYUAN_BASE_URL: str = "https://tokenhub.tencentmaas.com/v1"

    # Baidu Qianfan
    QIANFAN_API_KEY: str = ""
    QIANFAN_BASE_URL: str = "https://qianfan.baidubce.com/v2"

    # Zhipu AI
    ZHIPU_API_KEY: str = ""
    ZHIPU_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4"

    LLM_PROVIDER: str = "dashscope"
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen-plus"
    LLM_EMBEDDING_MODEL: str = "text-embedding-v4"
    LLM_EMBEDDING_API_KEY: str = ""
    LLM_EMBEDDING_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_EMBEDDING_DIM: int = 1024
    LLM_MAX_TOKENS: int = 2048
    LLM_TEMPERATURE: float = 0.7
    LLM_RERANK_MODEL: str = "gte-rerank-v2"

    # Vector Store
    VECTOR_STORE_TYPE: str = "milvus"
    VECTOR_FAISS_INDEX_PATH: str = "./data/faiss_index"
    VECTOR_DIMENSION: int = 1024

    # Milvus
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_USER: str = ""
    MILVUS_PASSWORD: str = ""
    MILVUS_DB: str = "default"
    MILVUS_COLLECTION: str = "agentflow_chunks"

    # Neo4j (Graph RAG)
    NEO4J_URI: str = "neo4j://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""
    NEO4J_DATABASE: str = "neo4j"

    # Logging
    LOG_DIR: str = "../logs"
    LOG_LEVEL: str = "INFO"
    LOG_ROTATION: str = "10 MB"
    LOG_RETENTION: str = "30 days"

    # Default model list (comma-separated for auto-seed)
    LLM_MODELS: str = "qwen-plus"

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


def load_settings() -> Settings:
    """从 settings.toml 和 .env 加载配置"""
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