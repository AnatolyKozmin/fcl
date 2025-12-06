import aiosqlite
from pathlib import Path


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection: aiosqlite.Connection | None = None
    
    async def connect(self) -> None:
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)
        await self._create_tables()
    
    async def disconnect(self) -> None:
        if self._connection:
            await self._connection.close()
    
    @property
    def connection(self) -> aiosqlite.Connection:
        if not self._connection:
            raise RuntimeError("Database not connected")
        return self._connection
    
    async def _create_tables(self) -> None:
        await self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT NOT NULL,
                study_group TEXT NOT NULL,
                course INTEGER NOT NULL,
                vk_link TEXT NOT NULL,
                tg_link TEXT NOT NULL,
                phone TEXT NOT NULL,
                faculty TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'registered',
                created_at TEXT NOT NULL,
                confirmation_sent INTEGER NOT NULL DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS bot_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                registration_open INTEGER NOT NULL DEFAULT 1,
                max_registrations INTEGER NOT NULL DEFAULT 0
            );
            
            INSERT OR IGNORE INTO bot_settings (id, registration_open, max_registrations)
            VALUES (1, 1, 0);
        """)
        await self.connection.commit()

