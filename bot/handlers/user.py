from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from bot.keyboards.user_kb import UserKeyboards
from bot.states.registration import RegistrationStates
from database.repositories import UserRepository, SettingsRepository

router = Router()


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    user_repo: UserRepository,
    settings_repo: SettingsRepository
):
    await state.clear()
    

    settings = await settings_repo.get()
    
    if not settings.registration_open:
        await message.answer(
            "❌ <b>Регистрация закрыта</b>\n\n"
            "К сожалению, регистрация на проект в данный момент недоступна. "
            "Следите за обновлениями!",
            parse_mode="HTML"
        )
        return
    

    existing_user = await user_repo.get_by_telegram_id(message.from_user.id)
    if existing_user:
        await message.answer(
            f"👋 <b>Привет, {existing_user.full_name}!</b>\n\n"
            f"Ты уже зарегистрирован на проект.\n"
            f"Статус: <b>{existing_user.status.value}</b>",
            parse_mode="HTML"
        )
        return
    
    await message.answer(
        "👋 <b>Привет!</b>\n\n"
        "Добро пожаловать в бота регистрации на проект!\n\n"
        "Нажми кнопку ниже, чтобы начать регистрацию.",
        reply_markup=UserKeyboards.get_start_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "📝 Зарегистрироваться")
async def start_registration(
    message: Message,
    state: FSMContext,
    user_repo: UserRepository,
    settings_repo: SettingsRepository
):

    settings = await settings_repo.get()
    
    if not settings.registration_open:
        await message.answer(
            "❌ <b>Регистрация закрыта</b>",
            parse_mode="HTML"
        )
        return
    

    existing_user = await user_repo.get_by_telegram_id(message.from_user.id)
    if existing_user:
        await message.answer(
            "Ты уже зарегистрирован!",
            parse_mode="HTML"
        )
        return
    
    await state.set_state(RegistrationStates.waiting_for_full_name)
    await message.answer(
        "📝 <b>Регистрация</b>\n\n"
        "Введи своё <b>ФИО</b> (полностью):",
        reply_markup=UserKeyboards.get_cancel_keyboard(),
        parse_mode="HTML"
    )