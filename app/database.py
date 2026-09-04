from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Integer,
    String,
    Text,
    delete,
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    memory_type: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    importance: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


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
            user.last_seen = datetime.now(UTC)

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


async def prune_history(telegram_user_id: int, keep: int):
    """Keep only the newest messages for one user."""
    async with SessionLocal() as session:
        old_ids = (
            select(Message.id)
            .where(Message.telegram_user_id == telegram_user_id)
            .order_by(Message.created_at.desc(), Message.id.desc())
            .offset(keep)
        )
        await session.execute(delete(Message).where(Message.id.in_(old_ids)))
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
        existing = await session.execute(
            select(Memory).where(
                Memory.telegram_user_id == telegram_user_id,
                Memory.memory_type == memory_type,
                Memory.content == content,
            )
        )
        if existing.scalar_one_or_none() is None:
            session.add(
                Memory(
                    telegram_user_id=telegram_user_id,
                    memory_type=memory_type,
                    content=content,
                    importance=importance,
                )
            )
        await session.commit()


async def prune_memories(telegram_user_id: int, keep: int):
    async with SessionLocal() as session:
        old_ids = (
            select(Memory.id)
            .where(Memory.telegram_user_id == telegram_user_id)
            .order_by(Memory.importance.desc(), Memory.created_at.desc(), Memory.id.desc())
            .offset(keep)
        )
        await session.execute(delete(Memory).where(Memory.id.in_(old_ids)))
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
        await session.execute(
            delete(Message).where(Message.telegram_user_id == telegram_user_id)
        )
        await session.commit()


async def clear_memories(telegram_user_id: int):
    async with SessionLocal() as session:
        await session.execute(
            delete(Memory).where(Memory.telegram_user_id == telegram_user_id)
        )
        await session.commit()


async def delete_user_data(telegram_user_id: int):
    """Delete all locally stored data associated with a Telegram user."""
    async with SessionLocal() as session:
        await session.execute(
            delete(Message).where(Message.telegram_user_id == telegram_user_id)
        )
        await session.execute(
            delete(Memory).where(Memory.telegram_user_id == telegram_user_id)
        )
        await session.execute(delete(User).where(User.telegram_id == telegram_user_id))
        await session.commit()
