from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    gender = State()
    target_gender = State()
    age = State()
    city = State()
    bio = State()
    avatar_choice = State()
    rename = State()

class SendLikeMessageStates(StatesGroup):
    message = State()

class EditProfileStates(StatesGroup):
    bio = State()
    photo = State()
    city = State()
    target_gender = State()
    name = State()
    age = State()

class SearchFilterStates(StatesGroup):
    custom_city = State()
    custom_age = State()

class PersonalPasswordStates(StatesGroup):
    setting_new_password = State()

