from database.database import Database
from database.models import BotSettings


class SettingsRepository:
    def __init__(self, db: Database):
        self.db = db
    
    async def get(self) -> BotSettings:
        cursor = await self.db.connection.execute(
            "SELECT registration_open, max_registrations FROM bot_settings WHERE id = 1"
        )
        row = await cursor.fetchone()
        if row:
            return BotSettings.from_row(row)
        return BotSettings()
    
    async def set_registration_open(self, is_open: bool) -> None:
        await self.db.connection.execute(
            "UPDATE bot_settings SET registration_open = ? WHERE id = 1",
            (int(is_open),)
        )
        await self.db.connection.commit()
    
    async def set_max_registrations(self, max_reg: int) -> None:
        await self.db.connection.execute(
            "UPDATE bot_settings SET max_registrations = ? WHERE id = 1",
            (max_reg,)
        )
        await self.db.connection.commit()
    
    async def is_registration_open(self) -> bool:
        settings = await self.get()
        return settings.registration_open
    
    async def get_max_registrations(self) -> int:
        settings = await self.get()
        return settings.max_registrations

