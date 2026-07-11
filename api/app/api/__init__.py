from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.models import router as models_router
from app.api.v1.rag import router as rag_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/v1")
api_router.include_router(users_router, prefix="/v1")
api_router.include_router(knowledge_router, prefix="/v1")
api_router.include_router(models_router, prefix="/v1")
api_router.include_router(rag_router, prefix="/v1")
