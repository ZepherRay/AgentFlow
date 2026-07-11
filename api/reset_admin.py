import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        u = result.scalar_one_or_none()
        if not u:
            print("admin not found, creating")
            u = User(username="admin", email="admin@admin.com", hashed_password=hash_password("admin123"), nickname="Admin", is_superuser=True)
            db.add(u)
        else:
            print(f"admin exists id={u.id}, resetting password")
            u.hashed_password = hash_password("admin123")
        await db.commit()
        print("OK, new hash:", u.hashed_password[:30])

asyncio.run(main())
