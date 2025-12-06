from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.keyboards.admin_kb import AdminKeyboards
from bot.keyboards.user_kb import UserKeyboards
from database.models import UserStatus
from database.repositories import UserRepository, SettingsRepository
from services.google_sheets import GoogleSheetsService
from config import Config

router = Router()


class AdminStates(StatesGroup):
    waiting_for_limit = State()
    waiting_for_delete_id = State()


def is_admin(user_id: int, config: Config) -> bool:
    return user_id in config.bot.admin_ids


@router.message(Command("admin"))
async def cmd_admin(message: Message, config: Config):
    if not is_admin(message.from_user.id, config):
        await message.answer("❌ У тебя нет доступа к админ-панели.")
        return
    
    await message.answer(
        "🔧 <b>Админ-панель</b>\n\n"
        "Выбери действие:",
        reply_markup=AdminKeyboards.get_admin_panel(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, config: Config, state: FSMContext):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    await state.clear()
    await callback.message.edit_text(
        "🔧 <b>Админ-панель</b>\n\n"
        "Выбери действие:",
        reply_markup=AdminKeyboards.get_admin_panel(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: CallbackQuery, config: Config, state: FSMContext):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    await state.clear()
    await callback.message.edit_text(
        "🔧 <b>Админ-панель</b>\n\n"
        "Выбери действие:",
        reply_markup=AdminKeyboards.get_admin_panel(),
        parse_mode="HTML"
    )


# Statistics
@router.callback_query(F.data == "admin_stats")
async def admin_stats(
    callback: CallbackQuery,
    config: Config,
    user_repo: UserRepository,
    settings_repo: SettingsRepository
):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    settings = await settings_repo.get()
    total = await user_repo.get_total_count()
    registered = len(await user_repo.get_all(UserStatus.REGISTERED))
    reserve = len(await user_repo.get_all(UserStatus.RESERVE))
    confirmed = len(await user_repo.get_all(UserStatus.CONFIRMED))
    declined = len(await user_repo.get_all(UserStatus.DECLINED))
    
    reg_status = "🟢 Открыта" if settings.registration_open else "🔴 Закрыта"
    limit_text = str(settings.max_registrations) if settings.max_registrations > 0 else "Без лимита"
    
    await callback.message.edit_text(
        f"📊 <b>Статистика</b>\n\n"
        f"📝 Регистрация: {reg_status}\n"
        f"👥 Лимит мест: {limit_text}\n\n"
        f"📌 <b>Всего записей:</b> {total}\n"
        f"✅ Зарегистрировано: {registered}\n"
        f"📋 В резерве: {reserve}\n"
        f"✅ Подтвердили: {confirmed}\n"
        f"❌ Отказались: {declined}",
        reply_markup=AdminKeyboards.get_back_button(),
        parse_mode="HTML"
    )


# Settings
@router.callback_query(F.data == "admin_settings")
async def admin_settings(
    callback: CallbackQuery,
    config: Config,
    settings_repo: SettingsRepository
):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    settings = await settings_repo.get()
    
    await callback.message.edit_text(
        "⚙️ <b>Настройки регистрации</b>\n\n"
        "Выбери параметр для изменения:",
        reply_markup=AdminKeyboards.get_settings_panel(
            settings.registration_open,
            settings.max_registrations
        ),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_toggle_registration")
async def admin_toggle_registration(
    callback: CallbackQuery,
    config: Config,
    settings_repo: SettingsRepository
):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    settings = await settings_repo.get()
    new_status = not settings.registration_open
    await settings_repo.set_registration_open(new_status)
    
    status_text = "открыта" if new_status else "закрыта"
    await callback.answer(f"Регистрация {status_text}")
    
    # Refresh settings panel
    settings = await settings_repo.get()
    await callback.message.edit_reply_markup(
        reply_markup=AdminKeyboards.get_settings_panel(
            settings.registration_open,
            settings.max_registrations
        )
    )


@router.callback_query(F.data == "admin_set_limit")
async def admin_set_limit(callback: CallbackQuery, config: Config, state: FSMContext):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_for_limit)
    await callback.message.edit_text(
        "🔢 <b>Установка лимита регистраций</b>\n\n"
        "Введи максимальное количество участников\n"
        "(0 = без лимита):",
        reply_markup=AdminKeyboards.get_cancel_button(),
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_for_limit)
async def process_limit(
    message: Message,
    state: FSMContext,
    config: Config,
    settings_repo: SettingsRepository,
    user_repo: UserRepository,
    bot: Bot
):
    if not is_admin(message.from_user.id, config):
        return
    
    try:
        limit = int(message.text.strip())
        if limit < 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Введи корректное число (0 или больше)")
        return
    
    await settings_repo.set_max_registrations(limit)
    await state.clear()
    
    # Update statuses if limit changed
    if limit > 0:
        registered_users = await user_repo.get_all(UserStatus.REGISTERED)
        for i, user in enumerate(registered_users):
            if i >= limit:
                await user_repo.update_status(user.id, UserStatus.RESERVE)
                # Notify user
                try:
                    await bot.send_message(
                        user.telegram_id,
                        "📋 К сожалению, количество мест ограничено, "
                        "и ты был перемещён в резерв. Мы сообщим, если появится место!"
                    )
                except Exception:
                    pass
    
    await message.answer(
        f"✅ Лимит установлен: {limit if limit > 0 else 'Без лимита'}",
        reply_markup=AdminKeyboards.get_back_button(),
        parse_mode="HTML"
    )


# Users management
@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery, config: Config):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "👥 <b>Управление участниками</b>\n\n"
        "Выбери категорию:",
        reply_markup=AdminKeyboards.get_users_panel(),
        parse_mode="HTML"
    )


async def show_users_list(
    callback: CallbackQuery,
    users: list,
    title: str
):
    if not users:
        await callback.message.edit_text(
            f"📋 <b>{title}</b>\n\n"
            "Список пуст.",
            reply_markup=AdminKeyboards.get_back_button(),
            parse_mode="HTML"
        )
        return
    
    text = f"📋 <b>{title}</b>\n\n"
    for i, user in enumerate(users[:50], 1):  # Limit to 50 to avoid message length issues
        text += f"{i}. {user.full_name} ({user.study_group})\n   ID: {user.id} | @{user.username or 'no_username'}\n"
    
    if len(users) > 50:
        text += f"\n... и ещё {len(users) - 50} участников"
    
    await callback.message.edit_text(
        text,
        reply_markup=AdminKeyboards.get_back_button(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_users_all")
async def admin_users_all(callback: CallbackQuery, config: Config, user_repo: UserRepository):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    users = await user_repo.get_all()
    await show_users_list(callback, users, "Все участники")


@router.callback_query(F.data == "admin_users_registered")
async def admin_users_registered(callback: CallbackQuery, config: Config, user_repo: UserRepository):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    users = await user_repo.get_all(UserStatus.REGISTERED)
    await show_users_list(callback, users, "Зарегистрированные")


@router.callback_query(F.data == "admin_users_reserve")
async def admin_users_reserve(callback: CallbackQuery, config: Config, user_repo: UserRepository):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    users = await user_repo.get_all(UserStatus.RESERVE)
    await show_users_list(callback, users, "В резерве")


@router.callback_query(F.data == "admin_users_confirmed")
async def admin_users_confirmed(callback: CallbackQuery, config: Config, user_repo: UserRepository):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    users = await user_repo.get_all(UserStatus.CONFIRMED)
    await show_users_list(callback, users, "Подтвердившие участие")


@router.callback_query(F.data == "admin_users_declined")
async def admin_users_declined(callback: CallbackQuery, config: Config, user_repo: UserRepository):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    users = await user_repo.get_all(UserStatus.DECLINED)
    await show_users_list(callback, users, "Отказавшиеся")


@router.callback_query(F.data == "admin_delete_user")
async def admin_delete_user(callback: CallbackQuery, config: Config, state: FSMContext):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    await state.set_state(AdminStates.waiting_for_delete_id)
    await callback.message.edit_text(
        "🗑 <b>Удаление участника</b>\n\n"
        "Введи ID участника для удаления\n"
        "(ID можно посмотреть в списке участников):",
        reply_markup=AdminKeyboards.get_cancel_button(),
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_for_delete_id)
async def process_delete_user(
    message: Message,
    state: FSMContext,
    config: Config,
    user_repo: UserRepository,
    settings_repo: SettingsRepository,
    bot: Bot
):
    if not is_admin(message.from_user.id, config):
        return
    
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введи корректный ID (число)")
        return
    
    deleted_user = await user_repo.delete(user_id)
    await state.clear()
    
    if not deleted_user:
        await message.answer(
            "❌ Участник с таким ID не найден.",
            reply_markup=AdminKeyboards.get_back_button()
        )
        return
    
    # If deleted user was registered, promote someone from reserve
    if deleted_user.status == UserStatus.REGISTERED:
        reserve_user = await user_repo.get_first_reserve()
        if reserve_user:
            await user_repo.update_status(reserve_user.id, UserStatus.REGISTERED)
            # Notify promoted user
            try:
                await bot.send_message(
                    reserve_user.telegram_id,
                    "🎉 <b>Отличные новости!</b>\n\n"
                    "Освободилось место, и ты теперь зарегистрирован на проект! "
                    "Ждём тебя!",
                    parse_mode="HTML"
                )
            except Exception:
                pass
    
    await message.answer(
        f"✅ Участник {deleted_user.full_name} удалён.",
        reply_markup=AdminKeyboards.get_back_button()
    )


# Broadcast confirmation
@router.callback_query(F.data == "admin_broadcast_confirm")
async def admin_broadcast_confirm(
    callback: CallbackQuery,
    config: Config,
    user_repo: UserRepository
):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    users = await user_repo.get_users_for_confirmation()
    
    await callback.message.edit_text(
        f"📢 <b>Рассылка подтверждения присутствия</b>\n\n"
        f"Будет отправлено сообщение с вопросом о присутствии\n"
        f"<b>{len(users)} участникам</b>\n\n"
        f"Подтвердить рассылку?",
        reply_markup=AdminKeyboards.get_confirm_broadcast(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_confirm_broadcast")
async def do_broadcast_confirmation(
    callback: CallbackQuery,
    config: Config,
    user_repo: UserRepository,
    bot: Bot
):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    users = await user_repo.get_users_for_confirmation()
    
    await callback.message.edit_text(
        "📤 Рассылка начата...",
        parse_mode="HTML"
    )
    
    success = 0
    failed = 0
    
    for user in users:
        try:
            await bot.send_message(
                user.telegram_id,
                "👋 <b>Привет!</b>\n\n"
                "Завтра состоится проект. Подтверждаешь ли ты своё присутствие?",
                reply_markup=UserKeyboards.get_confirmation_keyboard(),
                parse_mode="HTML"
            )
            await user_repo.update_confirmation_sent(user.id, True)
            success += 1
        except Exception:
            failed += 1
    
    await callback.message.edit_text(
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"✅ Отправлено: {success}\n"
        f"❌ Ошибок: {failed}",
        reply_markup=AdminKeyboards.get_back_button(),
        parse_mode="HTML"
    )


# Export to Google Sheets
@router.callback_query(F.data == "admin_export")
async def admin_export(callback: CallbackQuery, config: Config):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📋 <b>Экспорт в Google Sheets</b>\n\n"
        "Выбери тип экспорта:",
        reply_markup=AdminKeyboards.get_export_panel(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_export_all")
async def admin_export_all(
    callback: CallbackQuery,
    config: Config,
    user_repo: UserRepository,
    sheets_service: GoogleSheetsService
):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text("📤 Экспорт данных...")
    
    try:
        users = await user_repo.get_all()
        await sheets_service.export_registrations(users)
        
        await callback.message.edit_text(
            f"✅ <b>Экспорт завершён</b>\n\n"
            f"Экспортировано записей: {len(users)}",
            reply_markup=AdminKeyboards.get_back_button(),
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ <b>Ошибка экспорта</b>\n\n"
            f"Проверь настройки Google Sheets.\n"
            f"Ошибка: {str(e)}",
            reply_markup=AdminKeyboards.get_back_button(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "admin_export_confirmation")
async def admin_export_confirmation(
    callback: CallbackQuery,
    config: Config,
    user_repo: UserRepository,
    sheets_service: GoogleSheetsService
):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    await callback.message.edit_text("📤 Экспорт данных...")
    
    try:
        confirmed = await user_repo.get_confirmed_users()
        declined = await user_repo.get_declined_users()
        
        await sheets_service.export_confirmations(confirmed, declined)
        
        await callback.message.edit_text(
            f"✅ <b>Экспорт завершён</b>\n\n"
            f"Подтвердили: {len(confirmed)}\n"
            f"Отказались: {len(declined)}",
            reply_markup=AdminKeyboards.get_back_button(),
            parse_mode="HTML"
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ <b>Ошибка экспорта</b>\n\n"
            f"Проверь настройки Google Sheets.\n"
            f"Ошибка: {str(e)}",
            reply_markup=AdminKeyboards.get_back_button(),
            parse_mode="HTML"
        )

