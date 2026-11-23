import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import (
    hash_password,
    hash_password_async,
    verify_password,
    verify_password_async,
)
from app.models.user import User
from app.schemas.user import UserCreate


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Look up user by case-insensitive normalized email."""
    normalized_email = email.strip().lower()
    stmt = select(User).where(User.email == normalized_email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    """Look up user by primary key UUID."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Create a new user with bcrypt-hashed password (offloaded to thread)."""
    normalized_email = user_in.email.strip().lower()
    hashed_pwd = await hash_password_async(user_in.password)

    user = User(
        email=normalized_email,
        password_hash=hashed_pwd,
        full_name=user_in.full_name.strip(),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    """Authenticate user with email and plain password (offloaded to thread)."""
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not await verify_password_async(password, user.password_hash):
        return None
    return user
