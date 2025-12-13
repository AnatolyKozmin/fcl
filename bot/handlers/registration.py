import re
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from bot.keyboards.user_kb import UserKeyboards
from bot.states.registration import RegistrationStates
from database.models import UserStatus
from database.repositories import UserRepository, SettingsRepository

router = Router()


# Cancel handler
@router.message(F.text == "❌ Отмена")
async def cancel_registration(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.clear()
    await message.answer(
        "❌ Регистрация отменена.\n\n"
        "Нажми /start чтобы начать заново.",
        reply_markup=ReplyKeyboardRemove()
    )


# Step 1: Full Name
@router.message(RegistrationStates.waiting_for_full_name)
async def process_full_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    
    # Validate: at least 2 words
    if len(full_name.split()) < 2:
        await message.answer(
            "❌ Пожалуйста, введи полное ФИО (минимум имя и фамилия).",
            reply_markup=UserKeyboards.get_cancel_keyboard()
        )
        return
    
    await state.update_data(full_name=full_name)
    await state.set_state(RegistrationStates.waiting_for_study_group)
    
    await message.answer(
        "📚 Введи свою <b>учебную группу</b>\n"
        "(Формат: ПМ25-1):",
        reply_markup=UserKeyboards.get_cancel_keyboard(),
        parse_mode="HTML"
    )


# Step 2: Study Group

@router.message(RegistrationStates.waiting_for_study_group)
async def process_study_group(message: Message, state: FSMContext):
    study_group = message.text.strip()
    
    # Простая проверка на пустоту и разумную длину
    if not study_group or len(study_group) > 30:
        await message.answer(
            "❌ Название группы слишком длинное или пустое.\n"
            "Введи корректное название своей учебной группы.",
            reply_markup=UserKeyboards.get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Приводим к верхнему регистру для единообразия
    study_group = study_group.upper()
    
    await state.update_data(study_group=study_group)
    await state.set_state(RegistrationStates.waiting_for_course)
    
    await message.answer(
        f"✅ Группа <b>{study_group}</b> сохранена!\n\n"
        "🎓 Выбери свой <b>курс</b>:",
        reply_markup=UserKeyboards.get_course_keyboard(),
        parse_mode="HTML"
    )


# Step 3: Course
@router.message(RegistrationStates.waiting_for_course)
async def process_course(message: Message, state: FSMContext):
    if message.text not in ["1", "2", "3", "4"]:
        await message.answer(
            "❌ Выбери курс, нажав на одну из кнопок (1-4).",
            reply_markup=UserKeyboards.get_course_keyboard()
        )
        return
    
    await state.update_data(course=int(message.text))
    await state.set_state(RegistrationStates.waiting_for_vk_link)
    
    await message.answer(
        "🔗 Введи <b>ссылку на свой профиль ВКонтакте</b>\n"
        "(Например: https://vk.com/id123456):",
        reply_markup=UserKeyboards.get_cancel_keyboard(),
        parse_mode="HTML"
    )


# Step 4: VK Link
@router.message(RegistrationStates.waiting_for_vk_link)
async def process_vk_link(message: Message, state: FSMContext):
    vk_link = message.text.strip()
    
    # Validate VK link
    if not re.match(r'^https?://(www\.)?vk\.com/', vk_link):
        await message.answer(
            "❌ Неверный формат ссылки.\n"
            "Введи ссылку в формате: <b>https://vk.com/...</b>",
            reply_markup=UserKeyboards.get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    await state.update_data(vk_link=vk_link)
    await state.set_state(RegistrationStates.waiting_for_tg_link)
    
    await message.answer(
        "📱 Введи <b>ссылку на свой Telegram</b>\n"
        "(Например: https://t.me/username или @username):",
        reply_markup=UserKeyboards.get_cancel_keyboard(),
        parse_mode="HTML"
    )


# Step 5: TG Link
@router.message(RegistrationStates.waiting_for_tg_link)
async def process_tg_link(message: Message, state: FSMContext):
    tg_link = message.text.strip()
    
    # Validate TG link or username
    if not (re.match(r'^https?://(www\.)?t\.me/', tg_link) or re.match(r'^@[\w]+$', tg_link)):
        await message.answer(
            "❌ Неверный формат.\n"
            "Введи ссылку в формате: <b>https://t.me/username</b> или <b>@username</b>",
            reply_markup=UserKeyboards.get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Convert @username to link
    if tg_link.startswith("@"):
        tg_link = f"https://t.me/{tg_link[1:]}"
    
    await state.update_data(tg_link=tg_link)
    await state.set_state(RegistrationStates.waiting_for_phone)
    
    await message.answer(
        "📞 Введи свой <b>номер телефона</b>\n"
        "(Например: +79001234567):",
        reply_markup=UserKeyboards.get_cancel_keyboard(),
        parse_mode="HTML"
    )


# Step 6: Phone
@router.message(RegistrationStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    
    # Clean phone number
    phone_clean = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Validate phone format
    if not re.match(r'^(\+7|8|7)\d{10}$', phone_clean):
        await message.answer(
            "❌ Неверный формат номера.\n"
            "Введи номер в формате: <b>+79001234567</b>",
            reply_markup=UserKeyboards.get_cancel_keyboard(),
            parse_mode="HTML"
        )
        return
    
    # Normalize to +7 format
    if phone_clean.startswith("8"):
        phone_clean = "+7" + phone_clean[1:]
    elif phone_clean.startswith("7"):
        phone_clean = "+" + phone_clean
    
    await state.update_data(phone=phone_clean)
    await state.set_state(RegistrationStates.waiting_for_faculty)
    
    await message.answer(
        "🏛 Выбери свой <b>факультет</b>:",
        reply_markup=UserKeyboards.get_faculty_keyboard(),
        parse_mode="HTML"
    )


# Step 7: Faculty
@router.message(RegistrationStates.waiting_for_faculty)
async def process_faculty(message: Message, state: FSMContext):
    faculties = ["ИТиАБД", "МЭО", "ФЭБ", "СНиМК", "НАБ", "ВШУ", "ФФ", "ЮФ"]
    
    if message.text not in faculties:
        await message.answer(
            "❌ Выбери факультет, нажав на одну из кнопок.",
            reply_markup=UserKeyboards.get_faculty_keyboard()
        )
        return
    
    await state.update_data(faculty=message.text)
    await state.set_state(RegistrationStates.waiting_for_source)
    
    await message.answer(
        "📢 <b>Откуда ты узнал о проекте?</b>",
        reply_markup=UserKeyboards.get_source_keyboard(),
        parse_mode="HTML"
    )


# Step 8: Source
@router.message(RegistrationStates.waiting_for_source)
async def process_source(message: Message, state: FSMContext):
    sources = [
        "ВК-группа проекта",
        "ВК/Тг информера факультета",
        "От одногруппников",
        "От Координатора"
    ]
    
    if message.text not in sources:
        await message.answer(
            "❌ Выбери вариант, нажав на одну из кнопок.",
            reply_markup=UserKeyboards.get_source_keyboard()
        )
        return
    
    await state.update_data(source=message.text)
    await state.set_state(RegistrationStates.waiting_for_consent)
    
    await message.answer(
        "📋 <b>Согласие на обработку персональных данных</b>\n\n"
        "Нажимая кнопку «Согласен», ты даёшь согласие на обработку "
        "своих персональных данных в соответствии с законодательством РФ.",
        reply_markup=UserKeyboards.get_consent_keyboard(),
        parse_mode="HTML"
    )


# Step 9: Consent and final registration
@router.message(RegistrationStates.waiting_for_consent)
async def process_consent(
    message: Message,
    state: FSMContext,
    user_repo: UserRepository,
    settings_repo: SettingsRepository
):
    if message.text != "✅ Согласен":
        await message.answer(
            "❌ Для завершения регистрации необходимо дать согласие.",
            reply_markup=UserKeyboards.get_consent_keyboard()
        )
        return
    
    data = await state.get_data()
    await state.clear()
    
    # Check registration limits
    settings = await settings_repo.get()
    registered_count = await user_repo.get_registered_count()
    
    # Determine status based on limit
    if settings.max_registrations > 0 and registered_count >= settings.max_registrations:
        status = UserStatus.RESERVE
        status_text = "📋 <b>В резерве</b>"
        extra_message = (
            "\n\nК сожалению, все места уже заняты, но ты добавлен в резерв. "
            "Если кто-то откажется, мы тебе сообщим!"
        )
    else:
        status = UserStatus.REGISTERED
        status_text = "✅ <b>Зарегистрирован</b>"
        extra_message = ""
    
    # Create user
    try:
        user = await user_repo.create(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            full_name=data["full_name"],
            study_group=data["study_group"],
            course=data["course"],
            vk_link=data["vk_link"],
            tg_link=data["tg_link"],
            phone=data["phone"],
            faculty=data["faculty"],
            source=data["source"],
            status=status
        )
        
        await message.answer(
            f"🎉 <b>Ты успешно зарегистрировался!</b>{extra_message}\n\n"
            f"📌 <b>Твои данные:</b>\n"
            f"👤 ФИО: {user.full_name}\n"
            f"📚 Группа: {user.study_group}\n"
            f"🎓 Курс: {user.course}\n"
            f"🏛 Факультет: {user.faculty}\n"
            f"📊 Статус: {status_text}",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка при регистрации. Попробуй позже или обратись к координатору.",
            reply_markup=ReplyKeyboardRemove()
        )

