from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserOut, ChangePassword
from app.core.response import ResponseModel
from app.core.security import get_current_user, hash_password, verify_password

router = APIRouter(prefix="/users", tags=["用户"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=ResponseModel[UserOut])
async def create_user(req: UserCreate, db: AsyncSession = Depends(get_db)):
    # 1 获取参数
    username = req.username
    email = req.email
    password = req.password
    nickname = req.nickname

    # 2 过滤参数
    username = username.strip().lower()
    email = email.strip().lower()
    nickname = nickname.strip()

    # 3 操作数据库
    # 3.1 根据用户名查询 users 表数据
    result = await db.execute(select(User).where(User.username == username))
    existing = result.scalar_one_or_none()

    # 3.2 判断用户是否存在  存在则返回用户已存在
    if existing:
        raise HTTPException(status_code=400, detail="用户已存在！")

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


@router.put("/me", response_model=ResponseModel[UserOut])
async def update_me(
    req: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1 获取参数
    user_id = int(current_user["sub"])
    update_data = req.model_dump(exclude_unset=True)

    # 2 过滤参数
    if "email" in update_data:
        update_data["email"] = update_data["email"].strip().lower()
    if "nickname" in update_data:
        update_data["nickname"] = update_data["nickname"].strip()

    # 3 操作数据库
    # 3.1 根据用户 ID 查询 users 表数据
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    # 3.2 判断用户是否存在  不存在就返回用户不存在
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在！")

    # 3.3 存在则继续 更新用户字段
    for key, value in update_data.items():
        setattr(user, key, value)
    await db.flush()
    await db.refresh(user)

    # 4 返回数据
    return ResponseModel.ok(data=UserOut.model_validate(user))


@router.post("/me/change-password", response_model=ResponseModel)
async def change_password(
    req: ChangePassword,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1 获取参数
    user_id = int(current_user["sub"])
    old_password = req.old_password
    new_password = req.new_password
    confirm_password = req.confirm_password

    # 2 过滤参数（无需过滤）

    # 3 操作数据库
    # 3.1 根据用户 ID 查询 users 表数据
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    # 3.2 判断用户是否存在  不存在就返回用户不存在
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在！")

    # 3.3 存在则继续 判断旧密码是否正确
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="旧密码错误！")

    # 3.4 旧密码正确则继续 判断新密码是否一致
    if new_password != confirm_password:
        raise HTTPException(status_code=400, detail="两次密码不一致！")

    # 3.5 一致则继续 更新密码
    user.hashed_password = hash_password(new_password)
    await db.flush()

    # 4 返回数据
    return ResponseModel.ok(message="密码修改成功")