import hashlib
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.core.database import get_db
from api.models import APIKey, User
from api.schemas.auth import RegisterRequest, RegisterResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> RegisterResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(id=str(uuid.uuid4()), email=body.email)
    db.add(user)

    raw_key = secrets.token_urlsafe(32)
    api_key = APIKey(
        id=str(uuid.uuid4()),
        user_id=user.id,
        name="default",
        key_hash=hash_api_key(raw_key),
    )
    db.add(api_key)
    await db.commit()

    return RegisterResponse(
        email=body.email,
        api_key=raw_key,
        credits=user.credits,
        message="Store this key safely — it will not be shown again.",
    )
