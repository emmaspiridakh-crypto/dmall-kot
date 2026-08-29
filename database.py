import aiosqlite

DB_PATH = "dmbot.db"


class Database:
    _conn: aiosqlite.Connection = None

    @classmethod
    async def init(cls):
        cls._conn = await aiosqlite.connect(DB_PATH)
        await cls._conn.execute("""
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id      TEXT PRIMARY KEY,
                perms_role_id TEXT,
                log_channel_id TEXT
            )
        """)
        await cls._conn.commit()

    @classmethod
    async def _ensure_row(cls, guild_id: str):
        await cls._conn.execute(
            "INSERT OR IGNORE INTO guild_config (guild_id) VALUES (?)", (guild_id,)
        )
        await cls._conn.commit()

    @classmethod
    async def set_perms_role(cls, guild_id: str, role_id: str):
        await cls._ensure_row(guild_id)
        await cls._conn.execute(
            "UPDATE guild_config SET perms_role_id = ? WHERE guild_id = ?",
            (role_id, guild_id)
        )
        await cls._conn.commit()

    @classmethod
    async def get_perms_role(cls, guild_id: str):
        cur = await cls._conn.execute(
            "SELECT perms_role_id FROM guild_config WHERE guild_id = ?", (guild_id,)
        )
        row = await cur.fetchone()
        return row[0] if row else None

    @classmethod
    async def set_log_channel(cls, guild_id: str, channel_id: str):
        await cls._ensure_row(guild_id)
        await cls._conn.execute(
            "UPDATE guild_config SET log_channel_id = ? WHERE guild_id = ?",
            (channel_id, guild_id)
        )
        await cls._conn.commit()

    @classmethod
    async def get_log_channel(cls, guild_id: str):
        cur = await cls._conn.execute(
            "SELECT log_channel_id FROM guild_config WHERE guild_id = ?", (guild_id,)
        )
        row = await cur.fetchone()
        return row[0] if row else None
