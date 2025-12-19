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
    waiting_for_promote_count = State()


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


#################### СТАТКА #########################################
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


# Promote from reserve
@router.callback_query(F.data == "admin_promote_reserve")
async def admin_promote_reserve(
    callback: CallbackQuery,
    config: Config,
    user_repo: UserRepository,
    state: FSMContext
):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    reserve_users = await user_repo.get_all(UserStatus.RESERVE)
    declined_count = len(await user_repo.get_all(UserStatus.DECLINED))
    confirmed_count = len(await user_repo.get_all(UserStatus.CONFIRMED))
    registered_count = len(await user_repo.get_all(UserStatus.REGISTERED))
    
    if not reserve_users:
        await callback.message.edit_text(
            "📋 <b>Резерв пуст</b>\n\n"
            "Нет участников в резерве для добавления.",
            reply_markup=AdminKeyboards.get_back_button(),
            parse_mode="HTML"
        )
        return
    
    await state.set_state(AdminStates.waiting_for_promote_count)
    await callback.message.edit_text(
        f"📥 <b>Добавление из резерва</b>\n\n"
        f"📊 <b>Текущая статистика:</b>\n"
        f"✅ Подтвердили: {confirmed_count}\n"
        f"❌ Отказались: {declined_count}\n"
        f"⏳ Ждём ответа: {registered_count}\n"
        f"📋 В резерве: {len(reserve_users)}\n\n"
        f"<b>Сколько человек добавить из резерва?</b>\n"
        f"(максимум: {len(reserve_users)})",
        reply_markup=AdminKeyboards.get_cancel_button(),
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_for_promote_count)
async def process_promote_count(
    message: Message,
    state: FSMContext,
    config: Config,
    user_repo: UserRepository
):
    if not is_admin(message.from_user.id, config):
        return
    
    try:
        count = int(message.text.strip())
        if count <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("❌ Введи корректное число (больше 0)")
        return
    
    reserve_users = await user_repo.get_all(UserStatus.RESERVE)
    
    if count > len(reserve_users):
        await message.answer(
            f"❌ В резерве только {len(reserve_users)} человек.\n"
            f"Введи число от 1 до {len(reserve_users)}:"
        )
        return
    
    await state.clear()
    
    # Show confirmation
    await message.answer(
        f"📥 <b>Подтверждение</b>\n\n"
        f"Будет добавлено <b>{count}</b> человек из резерва.\n"
        f"Им будет отправлено уведомление.\n\n"
        f"Подтвердить?",
        reply_markup=AdminKeyboards.get_confirm_promote(count),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("admin_do_promote:"))
async def do_promote_reserve(
    callback: CallbackQuery,
    config: Config,
    user_repo: UserRepository,
    bot: Bot
):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    count = int(callback.data.split(":")[1])
    reserve_users = await user_repo.get_all(UserStatus.RESERVE)
    
    # Take first N users from reserve (sorted by registration date)
    users_to_promote = reserve_users[:count]
    
    await callback.message.edit_text("📤 Добавление участников...")
    
    success = 0
    failed = 0
    
    for user in users_to_promote:
        await user_repo.update_status(user.id, UserStatus.REGISTERED)
        # Notify user
        try:
            await bot.send_message(
                user.telegram_id,
                "🎉 <b>Отличные новости!</b>\n\n"
                "Ты переведён из резерва в основной список участников! "
                "Ждём тебя на проекте!",
                parse_mode="HTML"
            )
            success += 1
        except Exception:
            failed += 1
            success += 1  # User still promoted even if notification failed
    
    await callback.message.edit_text(
        f"✅ <b>Готово!</b>\n\n"
        f"Добавлено из резерва: {len(users_to_promote)}\n"
        f"Уведомлений отправлено: {success - failed}\n"
        f"Ошибок доставки: {failed}",
        reply_markup=AdminKeyboards.get_back_button(),
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
    

    if deleted_user.status == UserStatus.REGISTERED:
        reserve_user = await user_repo.get_first_reserve()
        if reserve_user:
            await user_repo.update_status(reserve_user.id, UserStatus.REGISTERED)

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


# Re-broadcast to non-responded users
@router.callback_query(F.data == "admin_rebroadcast_confirm")
async def admin_rebroadcast_confirm(
    callback: CallbackQuery,
    config: Config,
    user_repo: UserRepository
):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    # Get users who haven't responded (received message but status is still REGISTERED or RESERVE)
    users = await user_repo.get_users_without_response()
    
    if not users:
        await callback.message.edit_text(
            "📢 <b>Повторная рассылка</b>\n\n"
            "Нет участников, которым нужно отправить повторную рассылку.\n"
            "Все либо уже ответили, либо ещё не получили первую рассылку.",
            reply_markup=AdminKeyboards.get_back_button(),
            parse_mode="HTML"
        )
        return
    
    await callback.message.edit_text(
        f"🔄 <b>Повторная рассылка подтверждения</b>\n\n"
        f"Будет отправлено сообщение <b>{len(users)} участникам</b>, "
        f"которые получили первую рассылку, но ещё не ответили.\n\n"
        f"⚠️ <b>Внимание:</b> У них может быть несколько активных опросников, "
        f"но ответ засчитается только один раз.\n\n"
        f"Подтвердить повторную рассылку?",
        reply_markup=AdminKeyboards.get_confirm_rebroadcast(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_confirm_rebroadcast")
async def do_rebroadcast_confirmation(
    callback: CallbackQuery,
    config: Config,
    user_repo: UserRepository,
    bot: Bot
):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    # Get users who haven't responded
    users = await user_repo.get_users_without_response()
    
    await callback.message.edit_text(
        "📤 Повторная рассылка начата...",
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
            # Не сбрасываем confirmation_sent, чтобы знать что отправляли
            success += 1
        except Exception:
            failed += 1
    
    await callback.message.edit_text(
        f"✅ <b>Повторная рассылка завершена</b>\n\n"
        f"✅ Отправлено: {success}\n"
        f"❌ Ошибок: {failed}\n\n"
        f"💡 <b>Важно:</b> Если у пользователя несколько активных опросников, "
        f"ответ засчитается только один раз.",
        reply_markup=AdminKeyboards.get_back_button(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_confirm_broadcast_all")
async def do_broadcast_all(
    callback: CallbackQuery,
    config: Config,
    user_repo: UserRepository,
    bot: Bot
):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    # Get both new users and non-responded users
    new_users = await user_repo.get_users_for_confirmation()
    non_responded = await user_repo.get_users_without_response()
    
    # Create set of new user IDs for quick lookup
    new_user_ids = {user.id for user in new_users}
    
    all_users = new_users + non_responded
    
    await callback.message.edit_text(
        "📤 Рассылка начата...",
        parse_mode="HTML"
    )
    
    success_new = 0
    success_retry = 0
    failed = 0
    
    for user in all_users:
        try:
            await bot.send_message(
                user.telegram_id,
                "👋 <b>Привет!</b>\n\n"
                "Завтра состоится проект. Подтверждаешь ли ты своё присутствие?",
                reply_markup=UserKeyboards.get_confirmation_keyboard(),
                parse_mode="HTML"
            )
            # Устанавливаем confirmation_sent только для новых
            if user.id in new_user_ids:
                await user_repo.update_confirmation_sent(user.id, True)
                success_new += 1
            else:
                success_retry += 1
        except Exception:
            failed += 1
    
    await callback.message.edit_text(
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"🆕 Новым отправлено: {success_new}\n"
        f"⏳ Не ответили отправлено: {success_retry}\n"
        f"✅ Всего отправлено: {success_new + success_retry}\n"
        f"❌ Ошибок: {failed}\n\n"
        f"💡 <b>Важно:</b> Если у пользователя несколько активных опросников, "
        f"ответ засчитается только один раз.",
        reply_markup=AdminKeyboards.get_back_button(),
        parse_mode="HTML"
    )


# Broadcast to all (new + non-responded)
@router.callback_query(F.data == "admin_broadcast_all")
async def admin_broadcast_all(
    callback: CallbackQuery,
    config: Config,
    user_repo: UserRepository
):
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Нет доступа", show_alert=True)
        return
    
    # Get both new users and non-responded users
    new_users = await user_repo.get_users_for_confirmation()
    non_responded = await user_repo.get_users_without_response()
    total = len(new_users) + len(non_responded)
    
    if total == 0:
        await callback.message.edit_text(
            "📨 <b>Рассылка всем</b>\n\n"
            "Нет участников для рассылки.\n"
            "Все либо уже получили и ответили, либо ещё не зарегистрированы.",
            reply_markup=AdminKeyboards.get_back_button(),
            parse_mode="HTML"
        )
        return
    
    await callback.message.edit_text(
        f"📨 <b>Рассылка всем (новым + не ответили)</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"🆕 Новым (ещё не получали): {len(new_users)}\n"
        f"⏳ Не ответили (получали, но не ответили): {len(non_responded)}\n"
        f"📤 <b>Всего будет отправлено: {total}</b>\n\n"
        f"⚠️ <b>Внимание:</b> У тех, кто не ответил, может быть несколько активных опросников, "
        f"но ответ засчитается только один раз.\n\n"
        f"Подтвердить рассылку?",
        reply_markup=AdminKeyboards.get_confirm_broadcast_all(),
        parse_mode="HTML"
    )


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

