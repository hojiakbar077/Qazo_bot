from aiogram.fsm.state import State, StatesGroup

class AdminState(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_channel_add = State()
    waiting_for_channel_remove = State()
    waiting_for_admin_add = State()
    waiting_for_admin_remove = State()

class QazoHisobState(StatesGroup):
    choosing_range = State()
    choosing_years = State()
    choosing_months = State()
    choosing_days = State()

class QazoEditState(StatesGroup):
    selecting_prayer = State()
    editing_count = State()

class FaqStates(StatesGroup):
    waiting_for_question = State()
    waiting_for_answer = State()