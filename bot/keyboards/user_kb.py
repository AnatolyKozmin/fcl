from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


class UserKeyboards:
    
    @staticmethod
    def get_start_keyboard() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text="📝 Зарегистрироваться"))
        builder.adjust(1)
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def get_course_keyboard() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        for i in range(1, 5):
            builder.add(KeyboardButton(text=str(i)))
        builder.add(KeyboardButton(text="❌ Отмена"))
        builder.adjust(4, 1)
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def get_faculty_keyboard() -> ReplyKeyboardMarkup:
        faculties = [
            "ИТиАБД", "МЭО", "ФЭБ", "СНиМК",
            "НАБ", "ФШУ", "ФФ", "ЮФ"
        ]
        builder = ReplyKeyboardBuilder()
        for faculty in faculties:
            builder.add(KeyboardButton(text=faculty))
        builder.add(KeyboardButton(text="❌ Отмена"))
        builder.adjust(4, 4, 1)
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def get_source_keyboard() -> ReplyKeyboardMarkup:
        sources = [
            "ВК-группа проекта",
            "ВК/Тг информера факультета",
            "От одногруппников",
            "От Координатора"
        ]
        builder = ReplyKeyboardBuilder()
        for source in sources:
            builder.add(KeyboardButton(text=source))
        builder.add(KeyboardButton(text="❌ Отмена"))
        builder.adjust(1)
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def get_consent_keyboard() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text="✅ Согласен"))
        builder.add(KeyboardButton(text="❌ Отмена"))
        builder.adjust(1)
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def get_cancel_keyboard() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.add(KeyboardButton(text="❌ Отмена"))
        return builder.as_markup(resize_keyboard=True)
    
    @staticmethod
    def get_confirmation_keyboard() -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="✅ Да, приду", callback_data="confirm_yes"),
            InlineKeyboardButton(text="❌ Нет, не смогу", callback_data="confirm_no")
        )
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def remove_keyboard() -> ReplyKeyboardMarkup:
        from aiogram.types import ReplyKeyboardRemove
        return ReplyKeyboardRemove()

