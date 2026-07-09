from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token


class AuthService:
    @staticmethod
    async def authenticate(db: AsyncSession, username: str, password: str) -> str | None:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            return None
        return create_access_token(data={"sub": str(user.id), "username": user.username})