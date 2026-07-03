import hashlib

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.models import APIKey

api_key_header = APIKeyHeader(name="X-API-Key")


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def verify_api_key(
    key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> APIKey:
    key_hash = hash_api_key(key)
    result = await db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return api_key
