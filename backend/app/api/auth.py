from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
from pydantic import BaseModel
from typing import List, Set
import uuid

from ..database import get_db
from ..models import User
from ..services.auth_service import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
blacklisted_tokens: Set[str] = set()


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if token in blacklisted_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_token(token)
    if user_id is None:
        raise credentials_exception
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


@router.post("/register")
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == request.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")

    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        id=str(uuid.uuid4()),
        username=request.username,
        email=request.email,
        hashed_password=get_password_hash(request.password),
    )
    db.add(user)
    await db.commit()
    return {"message": "User registered successfully"}


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat(),
        },
    }


@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at.isoformat(),
    }


@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    blacklisted_tokens.add(token)
    return {"message": "Successfully logged out"}


@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    access_token = create_access_token(
        data={"sub": current_user.id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
