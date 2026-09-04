import tempfile
import unittest
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.database as database


class DatabaseTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "test.db"
        database.engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        database.SessionLocal = async_sessionmaker(
            database.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        await database.init_database()

    async def asyncTearDown(self):
        await database.engine.dispose()
        self.temp_dir.cleanup()

    async def test_history_pruning(self):
        await database.save_message(7, "user", "one")
        await database.save_message(7, "assistant", "two")
        await database.prune_history(7, 1)
        history = await database.get_history(7, 10)
        self.assertEqual(history, [{"role": "assistant", "content": "two"}])

    async def test_memory_deduplication_and_data_deletion(self):
        await database.save_memory(7, "note", "same")
        await database.save_memory(7, "note", "same")
        self.assertEqual(len(await database.get_memories(7, 10)), 1)
        await database.delete_user_data(7)
        self.assertEqual(await database.get_memories(7, 10), [])
        self.assertEqual(await database.get_history(7, 10), [])
