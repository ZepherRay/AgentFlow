from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import os
import uuid

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.core.response import ResponseModel
from app.core.security import get_current_user, hash_password

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
    if "password" in update_data:
        update_data["hashed_password"] = hash_password(update_data.pop("password"))

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


@router.post("/me/avatar", response_model=ResponseModel[dict])
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1 获取参数
    user_id = int(current_user["sub"])

    # 2 验证文件
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择文件")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
        raise HTTPException(status_code=400, detail="只支持图片格式")

    # 3 保存文件
    # Must match the StaticFiles mount in main.py: os.path.dirname(__file__) = api/, then "uploads"
    api_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    upload_dir = os.path.join(api_root, "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 4 更新数据库
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在！")
    user.avatar = f"/uploads/avatars/{filename}"
    await db.commit()
    await db.refresh(user)

    # 5 返回数据
    return ResponseModel.ok(data={"url": user.avatar})