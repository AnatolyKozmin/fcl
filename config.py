import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    token: str
    admin_ids: list[int]


@dataclass
class DatabaseConfig:
    path: str = "data/bot.db"


@dataclass
class GoogleSheetsConfig:
    credentials_file: str
    spreadsheet_id: str


@dataclass
class Config:
    bot: BotConfig
    db: DatabaseConfig
    google_sheets: GoogleSheetsConfig


def load_config() -> Config:
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    admin_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]
    
    return Config(
        bot=BotConfig(
            token=os.getenv("BOT_TOKEN", ""),
            admin_ids=admin_ids
        ),
        db=DatabaseConfig(
            path=os.getenv("DATABASE_PATH", "data/bot.db")
        ),
        google_sheets=GoogleSheetsConfig(
            credentials_file=os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json"),
            spreadsheet_id=os.getenv("GOOGLE_SPREADSHEET_ID", "")
        )
    )

