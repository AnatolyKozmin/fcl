from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class AdminKeyboards:
    
    @staticmethod
    def get_admin_panel() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="⚙️ Настройки регистрации", callback_data="admin_settings"),
            InlineKeyboardButton(text="👥 Список участников", callback_data="admin_users"),
            InlineKeyboardButton(text="📢 Рассылка подтверждения", callback_data="admin_broadcast_confirm"),
            InlineKeyboardButton(text="📋 Экспорт в Google Sheets", callback_data="admin_export"),
        )
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def get_settings_panel(registration_open: bool, max_reg: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        reg_status = "🟢 Открыта" if registration_open else "🔴 Закрыта"
        builder.add(
            InlineKeyboardButton(
                text=f"Регистрация: {reg_status}",
                callback_data="admin_toggle_registration"
            ),
            InlineKeyboardButton(
                text=f"Лимит: {max_reg if max_reg > 0 else 'Без лимита'}",
                callback_data="admin_set_limit"
            ),
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")
        )
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def get_users_panel() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="📋 Все участники", callback_data="admin_users_all"),
            InlineKeyboardButton(text="✅ Зарегистрированные", callback_data="admin_users_registered"),
            InlineKeyboardButton(text="📋 В резерве", callback_data="admin_users_reserve"),
            InlineKeyboardButton(text="✅ Подтвердившие", callback_data="admin_users_confirmed"),
            InlineKeyboardButton(text="❌ Отказавшиеся", callback_data="admin_users_declined"),
            InlineKeyboardButton(text="🗑 Удалить участника", callback_data="admin_delete_user"),
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")
        )
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def get_back_button() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back"))
        return builder.as_markup()
    
    @staticmethod
    def get_cancel_button() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel"))
        return builder.as_markup()
    
    @staticmethod
    def get_confirm_broadcast() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="✅ Подтвердить рассылку", callback_data="admin_confirm_broadcast"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")
        )
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def get_export_panel() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="📋 Все регистрации", callback_data="admin_export_all"),
            InlineKeyboardButton(text="✅ Подтвердившие/Отказавшиеся", callback_data="admin_export_confirmation"),
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")
        )
        builder.adjust(1)
        return builder.as_markup()

