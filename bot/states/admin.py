from aiogram.fsm.state import State, StatesGroup

class AdminLoginStates(StatesGroup):
    password = State()

class AdminSettingsStates(StatesGroup):
    new_access_password = State()

class UserGateStates(StatesGroup):
    enter_password = State()
