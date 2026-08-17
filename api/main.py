"""AgentFlow API Server."""
import sys
import io

# Force UTF-8 for stdout/stderr (fix Windows GBK crash on Unicode chars)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from config import settings
from app.core.logger import setup_logger
from app.core.exceptions import register_exception_handlers
from app.db.session import engine, Base, AsyncSessionLocal
from app.api import api_router
from app.utils.neo4j_client import close_neo4j_driver
from app.models.model import Model
from app.models.user import User
from app.core.security import hash_password
from sqlalchemy import select, func


async def seed_default_admin():
    """Create initial admin when no users exist (Docker first boot)."""
    username = (settings.INIT_ADMIN_USERNAME or "").strip().lower()
    password = settings.INIT_ADMIN_PASSWORD or ""
    email = (settings.INIT_ADMIN_EMAIL or "").strip().lower()
    if not username or not password or not email:
        return
    async with AsyncSessionLocal() as db:
        count = await db.scalar(select(func.count()).select_from(User))
        if count and count > 0:
            return
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            nickname=settings.INIT_ADMIN_NICKNAME or "Admin",
            is_superuser=True,
        )
        db.add(user)
        await db.commit()


async def seed_default_models():
    """Auto-seed models from LLM_MODELS env. Upserts by name to keep in sync."""
    from sqlalchemy import text
    model_names = [m.strip() for m in settings.LLM_MODELS.split(",") if m.strip()]
    if not model_names:
        return
    provider = settings.LLM_PROVIDER or "dashscope"
    api_key = settings.LLM_API_KEY or settings.DASHSCOPE_API_KEY or ""
    async with AsyncSessionLocal() as db:
        for name in model_names:
            result = await db.execute(select(Model).where(Model.name == name))
            existing = result.scalar_one_or_none()
            if existing:
                continue  # already exists, skip
            model = Model(name=name, type="chat", provider=provider, api_key=api_key)
            db.add(model)
        await db.commit()



@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_default_models()
    await seed_default_admin()
    yield
    await close_neo4j_driver()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix="/api")

uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} v{settings.APP_VERSION}"}


@app.get("/health")
async def health():
    return {"status": "ok"}