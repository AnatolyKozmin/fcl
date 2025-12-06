from aiogram import Router
from bot.handlers.user import router as user_router
from bot.handlers.registration import router as registration_router
from bot.handlers.admin import router as admin_router
from bot.handlers.confirmation import router as confirmation_router


def get_all_routers() -> list[Router]:
    return [user_router, registration_router, admin_router, confirmation_router]

