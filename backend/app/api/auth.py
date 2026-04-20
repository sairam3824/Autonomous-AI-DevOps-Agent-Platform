from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_current_user, get_password_hash, verify_password
from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import TokenResponse, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


async def _parse_login_credentials(request: Request) -> UserLogin:
    content_type = request.headers.get("content-type", "").lower()

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        return UserLogin(
            email=str(form.get("username", form.get("email", ""))),
            password=str(form.get("password", "")),
        )

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid login payload") from exc

    return UserLogin.model_validate(payload)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        role="engineer",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    credentials = await _parse_login_credentials(request)
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return UserResponse.model_validate(current_user)
