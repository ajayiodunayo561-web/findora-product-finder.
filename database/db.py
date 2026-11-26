from __future__ import annotations
from contextlib import asynccontextmanager
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from config import get_settings
from database.models import Base, User, ConversationState

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        return
    _engine = create_async_engine(get_settings().sqlalchemy_url, echo=False, pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    if _session_factory is None:
        init_engine()
    assert _session_factory is not None
    async with _session_factory() as session:
        yield session


async def init_db() -> None:
    init_engine()
    assert _engine is not None
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def upsert_user(telegram_id: int, username: str | None, first_name: str | None) -> None:
    async with get_session() as s:
        existing = (await s.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()
        if existing:
            existing.username = username
            existing.first_name = first_name
        else:
            s.add(User(telegram_id=telegram_id, username=username, first_name=first_name))
        await s.commit()


async def get_state(telegram_id: int) -> ConversationState | None:
    async with get_session() as s:
        return (await s.execute(
            select(ConversationState).where(ConversationState.telegram_id == telegram_id)
        )).scalar_one_or_none()


async def set_state(telegram_id: int, *, market: str | None = None, category: str | None = None) -> None:
    async with get_session() as s:
        st = (await s.execute(
            select(ConversationState).where(ConversationState.telegram_id == telegram_id)
        )).scalar_one_or_none()
        if st is None:
            st = ConversationState(telegram_id=telegram_id)
            s.add(st)
        if market is not None:
            st.market = market
        if category is not None:
            st.category = category
        await s.commit()


async def reset_state(telegram_id: int) -> None:
    async with get_session() as s:
        st = (await s.execute(
            select(ConversationState).where(ConversationState.telegram_id == telegram_id)
        )).scalar_one_or_none()
        if st:
            st.market = None
            st.category = None
            await s.commit()
