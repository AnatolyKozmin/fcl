from aiogram import Router
from .user import router as user_router
from .registration import router as registration_router
from .admin import router as admin_router
from .confirmation import router as confirmation_router


def get_all_routers() -> list[Router]:
    return [user_router, registration_router, admin_router, confirmation_router]

