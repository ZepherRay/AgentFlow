from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.models import router as models_router
from app.api.v1.rag import router as rag_router
from app.api.v1.assistant import router as assistant_router
from app.api.v1.agents import router as agents_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.skills import router as skills_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/v1")
api_router.include_router(users_router, prefix="/v1")
api_router.include_router(knowledge_router, prefix="/v1")
api_router.include_router(models_router, prefix="/v1")
api_router.include_router(rag_router, prefix="/v1")
api_router.include_router(assistant_router, prefix="/v1")
api_router.include_router(agents_router, prefix="/v1")
api_router.include_router(workflows_router, prefix="/v1")
api_router.include_router(skills_router, prefix="/v1")
