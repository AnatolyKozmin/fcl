from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_study_group = State()
    waiting_for_course = State()
    waiting_for_vk_link = State()
    waiting_for_tg_link = State()
    waiting_for_phone = State()
    waiting_for_faculty = State()
    waiting_for_source = State()
    waiting_for_consent = State()

