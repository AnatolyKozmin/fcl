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
            InlineKeyboardButton(text="🔄 Повторная рассылка (не ответили)", callback_data="admin_rebroadcast_confirm"),
            InlineKeyboardButton(text="📨 Рассылка всем (новым + не ответили)", callback_data="admin_broadcast_all"),
            InlineKeyboardButton(text="💬 Рассылка текстового сообщения", callback_data="admin_text_broadcast"),
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
            InlineKeyboardButton(text="📥 Добавить из резерва", callback_data="admin_promote_reserve"),
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
    def get_confirm_broadcast_all() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="✅ Подтвердить рассылку всем", callback_data="admin_confirm_broadcast_all"),
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
    
    
    @staticmethod
    def get_confirm_promote(count: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text=f"✅ Добавить {count} чел.", callback_data=f"admin_do_promote:{count}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")
        )
        builder.adjust(1)
        return builder.as_markup()
    
    
    @staticmethod
    def get_confirm_rebroadcast() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="✅ Подтвердить повторную рассылку", callback_data="admin_confirm_rebroadcast"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")
        )
        builder.adjust(1)
        return builder.as_markup()
    
    
    @staticmethod
    def get_text_broadcast_recipients() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="👥 Всем участникам", callback_data="text_broadcast:all"),
            InlineKeyboardButton(text="✅ Зарегистрированным", callback_data="text_broadcast:registered"),
            InlineKeyboardButton(text="📋 В резерве", callback_data="text_broadcast:reserve"),
            InlineKeyboardButton(text="✅ Подтвердившим", callback_data="text_broadcast:confirmed"),
            InlineKeyboardButton(text="❌ Отказавшимся", callback_data="text_broadcast:declined"),
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")
        )
        builder.adjust(1)
        return builder.as_markup()
    
    
    @staticmethod
    def get_confirm_text_broadcast(recipient_type: str, count: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        recipient_names = {
            "all": "всем участникам",
            "registered": "зарегистрированным",
            "reserve": "в резерве",
            "confirmed": "подтвердившим",
            "declined": "отказавшимся"
        }
        recipient_name = recipient_names.get(recipient_type, "участникам")
        builder.add(
            InlineKeyboardButton(
                text=f"✅ Отправить ({count} чел.)",
                callback_data=f"text_broadcast_confirm:{recipient_type}"
            ),
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")
        )
        builder.adjust(1)
        return builder.as_markup()

