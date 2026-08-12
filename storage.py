"""FSM holatlarini Postgres'da saqlovchi storage.

MemoryStorage bilan bot qayta ishga tushganda (Railway deploy, restart) yarim qolgan
"qo'shish"/"qidirish" holati yo'qolib qolar edi. Bu storage holatni bazaga yozadi.
"""

import json
from typing import Any, Dict, Optional

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StateType, StorageKey

import db


def _build_key(key: StorageKey) -> str:
    return ":".join(
        str(part)
        for part in (key.bot_id, key.chat_id, key.thread_id or 0, key.user_id, key.destiny)
    )


class PostgresStorage(BaseStorage):
    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        value = state.state if isinstance(state, State) else state
        pool = await db.get_pool()
        if value is None:
            await pool.execute(
                """
                UPDATE fsm_storage SET state = NULL, updated_at = now() WHERE key = $1
                """,
                _build_key(key),
            )
            # Holat ham, ma'lumot ham bo'sh bo'lsa — keraksiz qatorni saqlab o'tirmaymiz
            await pool.execute(
                "DELETE FROM fsm_storage WHERE key = $1 AND state IS NULL AND data = '{}'::jsonb",
                _build_key(key),
            )
            return
        await pool.execute(
            """
            INSERT INTO fsm_storage (key, state) VALUES ($1, $2)
            ON CONFLICT (key) DO UPDATE SET state = EXCLUDED.state, updated_at = now()
            """,
            _build_key(key), value,
        )

    async def get_state(self, key: StorageKey) -> Optional[str]:
        pool = await db.get_pool()
        return await pool.fetchval("SELECT state FROM fsm_storage WHERE key = $1", _build_key(key))

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        pool = await db.get_pool()
        if not data:
            await pool.execute(
                "UPDATE fsm_storage SET data = '{}'::jsonb, updated_at = now() WHERE key = $1",
                _build_key(key),
            )
            await pool.execute(
                "DELETE FROM fsm_storage WHERE key = $1 AND state IS NULL AND data = '{}'::jsonb",
                _build_key(key),
            )
            return
        await pool.execute(
            """
            INSERT INTO fsm_storage (key, data) VALUES ($1, $2::jsonb)
            ON CONFLICT (key) DO UPDATE SET data = EXCLUDED.data, updated_at = now()
            """,
            _build_key(key), json.dumps(data),
        )

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        pool = await db.get_pool()
        raw = await pool.fetchval("SELECT data FROM fsm_storage WHERE key = $1", _build_key(key))
        if not raw:
            return {}
        return json.loads(raw) if isinstance(raw, str) else dict(raw)

    async def close(self) -> None:
        # Pool'ni main.py yopadi
        pass
