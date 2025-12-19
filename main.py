import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import load_config
from database import Database
from database.repositories import UserRepository, SettingsRepository
from bot.handlers import get_all_routers
from services.google_sheets import GoogleSheetsService


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():

    config = load_config()
    
    if not config.bot.token:
        logger.error("BOT_TOKEN is not set!")
        return

    db = Database(config.db.path)
    await db.connect()
    logger.info("Database connected")
    

    user_repo = UserRepository(db)
    settings_repo = SettingsRepository(db)
    
 
    sheets_service = GoogleSheetsService(
        config.google_sheets.credentials_file,
        config.google_sheets.spreadsheet_id
    )
    

    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())
    

    for router in get_all_routers():
        dp.include_router(router)
    

    dp["config"] = config
    dp["user_repo"] = user_repo
    dp["settings_repo"] = settings_repo
    dp["sheets_service"] = sheets_service
    
    try:
        logger.info("Bot starting...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await db.disconnect()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())

