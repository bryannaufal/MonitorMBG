"""Shared dependencies for API route handlers."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db


async def get_session(session: AsyncSession = Depends(get_db)) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for route handlers."""
    yield session


# TODO: Add auth dependencies
# async def get_current_user(token: str = Depends(oauth2_scheme)):
#     ...
