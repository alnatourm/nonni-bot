from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Integer,
    String,
    Text,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)

from .config import settings


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    memory_type: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    importance: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


engine = create_async_engine(settings.database_url, echo=False)

SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def get_or_create_user(
    telegram_id: int,
    first_name: str | None = None,
    username: str | None = None,
):
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                username=username,
            )
            session.add(user)
        else:
            user.first_name = first_name
            user.username = username
            user.last_seen = datetime.utcnow()

        await session.commit()
        return user


async def save_message(
    telegram_user_id: int,
    role: str,
    content: str,
):
    async with SessionLocal() as session:
        message = Message(
            telegram_user_id=telegram_user_id,
            role=role,
            content=content,
        )
        session.add(message)
        await session.commit()


async def get_history(
    telegram_user_id: int,
    limit: int = 20,
):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Message)
            .where(Message.telegram_user_id == telegram_user_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(reversed(result.scalars().all()))
        return [
            {"role": message.role, "content": message.content}
            for message in messages
        ]


async def save_memory(
    telegram_user_id: int,
    memory_type: str,
    content: str,
    importance: int = 1,
):
    async with SessionLocal() as session:
        memory = Memory(
            telegram_user_id=telegram_user_id,
            memory_type=memory_type,
            content=content,
            importance=importance,
        )
        session.add(memory)
        await session.commit()


async def get_memories(
    telegram_user_id: int,
    limit: int = 20,
):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Memory)
            .where(Memory.telegram_user_id == telegram_user_id)
            .order_by(Memory.importance.desc(), Memory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


async def clear_history(telegram_user_id: int):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Message).where(Message.telegram_user_id == telegram_user_id)
        )
        messages = result.scalars().all()
        for message in messages:
            await session.delete(message)
        await session.commit()
