import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

import asyncpg
from .config import load_settings


class Database:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=10)

    async def disconnect(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def execute(self, query: str, *args: Any) -> str:
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized")
        async with self._pool.acquire() as con:
            return await con.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> List[asyncpg.Record]:
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized")
        async with self._pool.acquire() as con:
            return await con.fetch(query, *args)

    async def fetchrow(self, query: str, *args: Any) -> Optional[asyncpg.Record]:
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized")
        async with self._pool.acquire() as con:
            return await con.fetchrow(query, *args)

    async def fetchval(self, query: str, *args: Any) -> Any:
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized")
        async with self._pool.acquire() as con:
            return await con.fetchval(query, *args)

    async def init_schema(self, schema_path: Path) -> None:
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized")
        sql = schema_path.read_text(encoding="utf-8")
        async with self._pool.acquire() as con:
            async with con.transaction():
                await con.execute(sql)


# Export a singleton Database instance for routers to import
_settings = load_settings()
db = Database(_settings["DATABASE_URL"])


