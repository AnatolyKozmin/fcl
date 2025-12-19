from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.models import UserStatus
from database.repositories import UserRepository

router = Router()


@router.callback_query(F.data == "confirm_yes")
async def confirm_attendance_yes(
    callback: CallbackQuery,
    user_repo: UserRepository
):
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("Ты не зарегистрирован!", show_alert=True)
        return
    
    # Проверка: если уже подтвердил или отказался, не менять статус повторно
    if user.status == UserStatus.CONFIRMED:
        await callback.answer("Ты уже подтвердил участие!", show_alert=True)
        await callback.message.edit_text(
            "✅ <b>Ты уже подтвердил участие!</b>\n\n"
            "Ждём тебя на проекте! 🎉",
            parse_mode="HTML"
        )
        return
    
    if user.status == UserStatus.DECLINED:
        # Если ранее отказался, но теперь подтверждает - обновляем статус
        await user_repo.update_status(user.id, UserStatus.CONFIRMED)
        await callback.message.edit_text(
            "✅ <b>Отлично!</b>\n\n"
            "Спасибо за подтверждение! Ждём тебя на проекте! 🎉",
            parse_mode="HTML"
        )
        await callback.answer("Участие подтверждено!")
        return
    
    await user_repo.update_status(user.id, UserStatus.CONFIRMED)
    
    await callback.message.edit_text(
        "✅ <b>Отлично!</b>\n\n"
        "Спасибо за подтверждение! Ждём тебя на проекте! 🎉",
        parse_mode="HTML"
    )
    await callback.answer("Участие подтверждено!")

  
@router.callback_query(F.data == "confirm_no")
async def confirm_attendance_no(
    callback: CallbackQuery,
    user_repo: UserRepository
):
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("Ты не зарегистрирован!", show_alert=True)
        return
    
    # Проверка: если уже отказался, не менять статус повторно
    if user.status == UserStatus.DECLINED:
        await callback.answer("Ты уже отказался от участия!", show_alert=True)
        await callback.message.edit_text(
            "😔 <b>Ты уже отказался от участия.</b>\n\n"
            "Спасибо, что предупредил. Надеемся увидеть тебя в следующий раз!",
            parse_mode="HTML"
        )
        return
    
    if user.status == UserStatus.CONFIRMED:
        # Если ранее подтвердил, но теперь отказывается - обновляем статус
        await user_repo.update_status(user.id, UserStatus.DECLINED)
        await callback.message.edit_text(
            "😔 <b>Очень жаль!</b>\n\n"
            "Спасибо, что предупредил. Надеемся увидеть тебя в следующий раз!",
            parse_mode="HTML"
        )
        await callback.answer("Отказ зафиксирован")
        return
    
    await user_repo.update_status(user.id, UserStatus.DECLINED)
    
    await callback.message.edit_text(
        "😔 <b>Очень жаль!</b>\n\n"
        "Спасибо, что предупредил. Надеемся увидеть тебя в следующий раз!",
        parse_mode="HTML"
    )
    await callback.answer("Отказ зафиксирован")

