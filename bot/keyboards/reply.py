from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard(has_lock: bool = False) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🔍 Поиск"), KeyboardButton(text="💬 Чаты")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="💌 Симпатии")]
    ]
    if has_lock:
        keyboard.append([KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="🔒 Заблокировать")])
    else:
        keyboard.append([KeyboardButton(text="⚙️ Настройки")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_in_chat_reply_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🚪 В меню"), KeyboardButton(text="💬 Чаты")],
        [KeyboardButton(text="🔥 Завершить чат")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text="❌ Отмена")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_skip_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="⏩ Пропустить")],
        [KeyboardButton(text="❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
