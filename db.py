import random
import string

import asyncpg

from config import DATABASE_URL
from seed_data import CATEGORIES

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return _pool


SCHEMA = """
CREATE TABLE IF NOT EXISTS families (
    id SERIAL PRIMARY KEY,
    invite_code TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    full_name TEXT,
    family_id INT REFERENCES families(id) ON DELETE SET NULL,
    role TEXT DEFAULT 'a_zo', -- 'asosiy' | 'yordamchi' | 'a_zo'
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    code INT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS entries (
    id SERIAL PRIMARY KEY,
    family_id INT REFERENCES families(id) ON DELETE CASCADE,
    category_id INT REFERENCES categories(id) ON DELETE CASCADE,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    content_type TEXT NOT NULL, -- text | photo | video | document | voice
    text_content TEXT,
    file_id TEXT,
    caption TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
"""


def _gen_invite_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


async def init_db() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA)
        for code, name, description in CATEGORIES:
            await conn.execute(
                """
                INSERT INTO categories (code, name, description)
                VALUES ($1, $2, $3)
                ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description
                """,
                code, name, description,
            )


async def get_user(telegram_id: int) -> asyncpg.Record | None:
    pool = await get_pool()
    return await pool.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)


async def create_user_with_new_family(telegram_id: int, full_name: str) -> asyncpg.Record:
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            code = _gen_invite_code()
            while await conn.fetchval("SELECT 1 FROM families WHERE invite_code = $1", code):
                code = _gen_invite_code()
            family = await conn.fetchrow(
                "INSERT INTO families (invite_code) VALUES ($1) RETURNING *", code
            )
            user = await conn.fetchrow(
                """
                INSERT INTO users (telegram_id, full_name, family_id, role)
                VALUES ($1, $2, $3, 'asosiy') RETURNING *
                """,
                telegram_id, full_name, family["id"],
            )
            return user


async def join_family(telegram_id: int, full_name: str, invite_code: str) -> asyncpg.Record | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        family = await conn.fetchrow(
            "SELECT * FROM families WHERE invite_code = $1", invite_code.strip().upper()
        )
        if not family:
            return None
        existing = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
        if existing:
            await conn.execute(
                "UPDATE users SET family_id = $1, role = 'yordamchi' WHERE telegram_id = $2",
                family["id"], telegram_id,
            )
        else:
            await conn.execute(
                """
                INSERT INTO users (telegram_id, full_name, family_id, role)
                VALUES ($1, $2, $3, 'yordamchi')
                """,
                telegram_id, full_name, family["id"],
            )
        return family


async def get_family_invite_code(family_id: int) -> str:
    pool = await get_pool()
    return await pool.fetchval("SELECT invite_code FROM families WHERE id = $1", family_id)


async def list_categories() -> list[asyncpg.Record]:
    pool = await get_pool()
    return await pool.fetch("SELECT * FROM categories ORDER BY code")


async def get_category(category_id: int) -> asyncpg.Record | None:
    pool = await get_pool()
    return await pool.fetchrow("SELECT * FROM categories WHERE id = $1", category_id)


async def add_entry(
    family_id: int,
    category_id: int,
    user_id: int,
    content_type: str,
    text_content: str | None = None,
    file_id: str | None = None,
    caption: str | None = None,
) -> None:
    pool = await get_pool()
    await pool.execute(
        """
        INSERT INTO entries (family_id, category_id, user_id, content_type, text_content, file_id, caption)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        family_id, category_id, user_id, content_type, text_content, file_id, caption,
    )


async def list_entries(family_id: int, category_id: int) -> list[asyncpg.Record]:
    pool = await get_pool()
    return await pool.fetch(
        """
        SELECT e.*, u.full_name FROM entries e
        LEFT JOIN users u ON u.id = e.user_id
        WHERE e.family_id = $1 AND e.category_id = $2
        ORDER BY e.created_at DESC
        """,
        family_id, category_id,
    )


async def count_entries(family_id: int, category_id: int) -> int:
    pool = await get_pool()
    return await pool.fetchval(
        "SELECT count(*) FROM entries WHERE family_id = $1 AND category_id = $2",
        family_id, category_id,
    )
