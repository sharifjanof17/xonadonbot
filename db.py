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


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


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
    language TEXT DEFAULT 'uz', -- 'uz' | 'ru'
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    code INT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    name_ru TEXT,
    description_ru TEXT,
    prompt TEXT,        -- "➕ Qo'shish" bosilganda so'raladigan matn
    prompt_ru TEXT
);

-- Eski bazalar uchun (Railway'dagi mavjud baza yangi ustunlarni shu yerdan oladi)
ALTER TABLE users ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'uz';
ALTER TABLE categories ADD COLUMN IF NOT EXISTS name_ru TEXT;
ALTER TABLE categories ADD COLUMN IF NOT EXISTS description_ru TEXT;
ALTER TABLE categories ADD COLUMN IF NOT EXISTS prompt TEXT;
ALTER TABLE categories ADD COLUMN IF NOT EXISTS prompt_ru TEXT;

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

CREATE INDEX IF NOT EXISTS entries_family_category_idx
    ON entries (family_id, category_id, created_at DESC);

-- FSM holatlari: bot qayta ishga tushganda ham yarim qolgan amal yo'qolmasligi uchun
CREATE TABLE IF NOT EXISTS fsm_storage (
    key TEXT PRIMARY KEY,
    state TEXT,
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT now()
);
"""

ENTRIES_PAGE_SIZE = 5


def _gen_invite_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


async def init_db() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA)
        for cat in CATEGORIES:
            await conn.execute(
                """
                INSERT INTO categories (code, name, description, name_ru, description_ru, prompt, prompt_ru)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    name_ru = EXCLUDED.name_ru,
                    description_ru = EXCLUDED.description_ru,
                    prompt = EXCLUDED.prompt,
                    prompt_ru = EXCLUDED.prompt_ru
                """,
                cat["code"], cat["name"], cat["description"],
                cat["name_ru"], cat["description_ru"], cat["prompt"], cat["prompt_ru"],
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


async def get_or_create_user(telegram_id: int, full_name: str) -> asyncpg.Record:
    """Foydalanuvchini qaytaradi; bo'lmasa unga yangi oila ochib beradi.

    Oilasi yo'q (family_id NULL) qolib ketgan foydalanuvchiga ham yangi oila ochadi,
    shunda hech qayerda family_id None bo'lib qolmaydi.
    """
    user = await get_user(telegram_id)
    if user is not None and user["family_id"] is not None:
        return user
    if user is None:
        return await create_user_with_new_family(telegram_id, full_name)

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            code = _gen_invite_code()
            while await conn.fetchval("SELECT 1 FROM families WHERE invite_code = $1", code):
                code = _gen_invite_code()
            family = await conn.fetchrow(
                "INSERT INTO families (invite_code) VALUES ($1) RETURNING *", code
            )
            return await conn.fetchrow(
                "UPDATE users SET family_id = $1, role = 'asosiy' WHERE telegram_id = $2 RETURNING *",
                family["id"], telegram_id,
            )


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


async def set_language(telegram_id: int, language: str) -> None:
    pool = await get_pool()
    await pool.execute(
        "UPDATE users SET language = $1 WHERE telegram_id = $2", language, telegram_id
    )


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


async def list_entries(
    family_id: int, category_id: int, limit: int = ENTRIES_PAGE_SIZE, offset: int = 0
) -> list[asyncpg.Record]:
    pool = await get_pool()
    return await pool.fetch(
        """
        SELECT e.*, u.full_name FROM entries e
        LEFT JOIN users u ON u.id = e.user_id
        WHERE e.family_id = $1 AND e.category_id = $2
        ORDER BY e.created_at DESC
        LIMIT $3 OFFSET $4
        """,
        family_id, category_id, limit, offset,
    )


async def count_entries(family_id: int, category_id: int) -> int:
    pool = await get_pool()
    return await pool.fetchval(
        "SELECT count(*) FROM entries WHERE family_id = $1 AND category_id = $2",
        family_id, category_id,
    )


async def get_entry(entry_id: int, family_id: int) -> asyncpg.Record | None:
    """Yozuvni qaytaradi. family_id shart — begona oilaning yozuviga tegib bo'lmasin."""
    pool = await get_pool()
    return await pool.fetchrow(
        """
        SELECT e.*, u.full_name, c.name AS category_name, c.name_ru AS category_name_ru FROM entries e
        LEFT JOIN users u ON u.id = e.user_id
        LEFT JOIN categories c ON c.id = e.category_id
        WHERE e.id = $1 AND e.family_id = $2
        """,
        entry_id, family_id,
    )


async def delete_entry(entry_id: int, family_id: int) -> bool:
    pool = await get_pool()
    result = await pool.execute(
        "DELETE FROM entries WHERE id = $1 AND family_id = $2", entry_id, family_id
    )
    return result.endswith(" 1")


async def search_entries(
    family_id: int, query: str, category_id: int | None = None, limit: int = 20
) -> list[asyncpg.Record]:
    """Matn va izohlar bo'yicha qidiradi. category_id berilsa — faqat shu toifa ichidan."""
    pool = await get_pool()
    # LIKE ning maxsus belgilarini qochiramiz, aks holda "%" hamma narsani topib beradi
    safe = query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{safe}%"
    return await pool.fetch(
        r"""
        SELECT e.*, u.full_name, c.name AS category_name, c.name_ru AS category_name_ru FROM entries e
        LEFT JOIN users u ON u.id = e.user_id
        LEFT JOIN categories c ON c.id = e.category_id
        WHERE e.family_id = $1
          AND ($2::int IS NULL OR e.category_id = $2)
          AND (e.text_content ILIKE $3 ESCAPE '\' OR e.caption ILIKE $3 ESCAPE '\')
        ORDER BY e.created_at DESC
        LIMIT $4
        """,
        family_id, category_id, pattern, limit,
    )


async def list_family_members(family_id: int) -> list[asyncpg.Record]:
    pool = await get_pool()
    return await pool.fetch(
        "SELECT * FROM users WHERE family_id = $1 ORDER BY created_at", family_id
    )
