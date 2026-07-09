from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserLogin, UserCreate, UserOut, TokenOut
from app.core.response import ResponseModel
from app.core.security import verify_password, create_access_token, hash_password, get_current_user

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=ResponseModel[TokenOut])
async def login(req: UserLogin, db: AsyncSession = Depends(get_db)):
    # 1 获取参数
    username = req.username
    password = req.password

    # 2 过滤参数
    username = username.strip().lower()

    # 3 操作数据库
    # 3.1 根据用户名查询 users 表数据
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    # 3.2 判断用户是否存在  不存在就返回用户不存在
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在！")

    # 3.3 存在则继续 判断密码是否正确  不正确则返回密码错误
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="密码不正确！")

    # 3.4 正确则继续 判断账号是否冻结  冻结则返回账号冻结
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被冻结！")

    # 4 返回数据
    token = create_access_token(data={"sub": str(user.id), "username": user.username})
    return ResponseModel.ok(data=TokenOut(access_token=token))


@router.post("/register", response_model=ResponseModel[UserOut])
async def register(req: UserCreate, db: AsyncSession = Depends(get_db)):
    # 1 获取参数
    username = req.username
    email = req.email
    password = req.password
    nickname = req.nickname

    # 2 过滤参数
    username = username.strip().lower()
    email = email.strip().lower()
    nickname = (nickname or "").strip() or username

    # 3 操作数据库
    # 3.1 检查用户名或邮箱是否已存在
    result = await db.execute(
        select(User).where(or_(User.username == username, User.email == email))
    )
    existing = result.scalar_one_or_none()

    # 3.2 判断用户是否存在  存在则返回对应提示
    if existing:
        if existing.username == username:
            raise HTTPException(status_code=400, detail="用户名已被注册！")
        else:
            raise HTTPException(status_code=400, detail="邮箱已被注册！")

    # 3.3 不存在则继续 创建新用户
    # 3.4 插入 users 表
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        nickname=nickname,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    # 4 返回数据
    return ResponseModel.ok(data=UserOut.model_validate(user))


@router.get("/me", response_model=ResponseModel[UserOut])
async def get_me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1 获取参数
    user_id = int(current_user["sub"])

    # 2 过滤参数（无需过滤）

    # 3 操作数据库
    # 3.1 根据用户 ID 查询 users 表数据
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    # 3.2 判断用户是否存在  不存在就返回用户不存在
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在！")

    # 4 返回数据
    return ResponseModel.ok(data=UserOut.model_validate(user))