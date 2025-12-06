from datetime import datetime
from typing import Optional
from database.database import Database
from database.models import User, UserStatus


class UserRepository:
    def __init__(self, db: Database):
        self.db = db
    
    async def create(
        self,
        telegram_id: int,
        username: Optional[str],
        full_name: str,
        study_group: str,
        course: int,
        vk_link: str,
        tg_link: str,
        phone: str,
        faculty: str,
        source: str,
        status: UserStatus = UserStatus.REGISTERED
    ) -> User:
        cursor = await self.db.connection.execute(
            """
            INSERT INTO users (
                telegram_id, username, full_name, study_group, course,
                vk_link, tg_link, phone, faculty, source, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id, username, full_name, study_group, course,
                vk_link, tg_link, phone, faculty, source, status.value,
                datetime.now().isoformat()
            )
        )
        await self.db.connection.commit()
        
        return await self.get_by_telegram_id(telegram_id)
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        cursor = await self.db.connection.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return User.from_row(row) if row else None
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        cursor = await self.db.connection.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return User.from_row(row) if row else None
    
    async def get_all(self, status: Optional[UserStatus] = None) -> list[User]:
        if status:
            cursor = await self.db.connection.execute(
                "SELECT * FROM users WHERE status = ? ORDER BY created_at ASC",
                (status.value,)
            )
        else:
            cursor = await self.db.connection.execute(
                "SELECT * FROM users ORDER BY created_at ASC"
            )
        rows = await cursor.fetchall()
        return [User.from_row(row) for row in rows]
    
    async def get_registered_count(self) -> int:
        """Get count of users who are registered (not in reserve)"""
        cursor = await self.db.connection.execute(
            "SELECT COUNT(*) FROM users WHERE status = ?",
            (UserStatus.REGISTERED.value,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0
    
    async def get_total_count(self) -> int:
        """Get total count of all users"""
        cursor = await self.db.connection.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0] if row else 0
    
    async def update_status(self, user_id: int, status: UserStatus) -> None:
        await self.db.connection.execute(
            "UPDATE users SET status = ? WHERE id = ?",
            (status.value, user_id)
        )
        await self.db.connection.commit()
    
    async def update_confirmation_sent(self, user_id: int, sent: bool = True) -> None:
        await self.db.connection.execute(
            "UPDATE users SET confirmation_sent = ? WHERE id = ?",
            (int(sent), user_id)
        )
        await self.db.connection.commit()
    
    async def delete(self, user_id: int) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if user:
            await self.db.connection.execute(
                "DELETE FROM users WHERE id = ?", (user_id,)
            )
            await self.db.connection.commit()
        return user
    
    async def delete_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            await self.db.connection.execute(
                "DELETE FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            await self.db.connection.commit()
        return user
    
    async def get_first_reserve(self) -> Optional[User]:
        """Get the first user in reserve (earliest registration)"""
        cursor = await self.db.connection.execute(
            """
            SELECT * FROM users 
            WHERE status = ? 
            ORDER BY created_at ASC 
            LIMIT 1
            """,
            (UserStatus.RESERVE.value,)
        )
        row = await cursor.fetchone()
        return User.from_row(row) if row else None
    
    async def get_users_for_confirmation(self) -> list[User]:
        """Get users who haven't received confirmation request yet"""
        cursor = await self.db.connection.execute(
            """
            SELECT * FROM users 
            WHERE status IN (?, ?) AND confirmation_sent = 0
            ORDER BY created_at ASC
            """,
            (UserStatus.REGISTERED.value, UserStatus.RESERVE.value)
        )
        rows = await cursor.fetchall()
        return [User.from_row(row) for row in rows]
    
    async def get_confirmed_users(self) -> list[User]:
        """Get users who confirmed attendance"""
        cursor = await self.db.connection.execute(
            "SELECT * FROM users WHERE status = ? ORDER BY created_at ASC",
            (UserStatus.CONFIRMED.value,)
        )
        rows = await cursor.fetchall()
        return [User.from_row(row) for row in rows]
    
    async def get_declined_users(self) -> list[User]:
        """Get users who declined attendance"""
        cursor = await self.db.connection.execute(
            "SELECT * FROM users WHERE status = ? ORDER BY created_at ASC",
            (UserStatus.DECLINED.value,)
        )
        rows = await cursor.fetchall()
        return [User.from_row(row) for row in rows]

