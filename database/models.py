from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class UserStatus(Enum):
    REGISTERED = "registered"
    RESERVE = "reserve"
    CONFIRMED = "confirmed"
    DECLINED = "declined"


@dataclass
class User:
    id: int
    telegram_id: int
    username: Optional[str]
    full_name: str
    study_group: str
    course: int
    vk_link: str
    tg_link: str
    phone: str
    faculty: str
    source: str
    status: UserStatus
    created_at: datetime
    confirmation_sent: bool = False
    
    @classmethod
    def from_row(cls, row: tuple) -> "User":
        return cls(
            id=row[0],
            telegram_id=row[1],
            username=row[2],
            full_name=row[3],
            study_group=row[4],
            course=row[5],
            vk_link=row[6],
            tg_link=row[7],
            phone=row[8],
            faculty=row[9],
            source=row[10],
            status=UserStatus(row[11]),
            created_at=datetime.fromisoformat(row[12]),
            confirmation_sent=bool(row[13])
        )


@dataclass
class BotSettings:
    registration_open: bool = True
    max_registrations: int = 0  # 0 = unlimited
    
    @classmethod
    def from_row(cls, row: tuple) -> "BotSettings":
        return cls(
            registration_open=bool(row[0]),
            max_registrations=row[1]
        )

