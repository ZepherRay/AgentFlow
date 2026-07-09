from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password


class UserService:
    @staticmethod
    async def create(db: AsyncSession, req: UserCreate) -> User:
        user = User(
            username=req.username,
            email=req.email,
            hashed_password=hash_password(req.password),
            nickname=req.nickname,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int | str) -> User | None:
        result = await db.execute(select(User).where(User.id == int(user_id)))
        return result.scalar_one_or_none()

    @staticmethod
    async def update(db: AsyncSession, user_id: int | str, req: UserUpdate) -> User:
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise ValueError("User not found")
        update_data = req.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        await db.flush()
        await db.refresh(user)
        return user