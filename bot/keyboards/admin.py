from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_main_keyboard(pass_enabled: bool) -> InlineKeyboardMarkup:
    lock_status = "🟢 ВКЛ" if pass_enabled else "🔴 ВЫКЛ"
    toggle_cb = "adm_toggle_pass:0" if pass_enabled else "adm_toggle_pass:1"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Общая аналитика", callback_data="adm_view:summary"),
                InlineKeyboardButton(text="⏱ Активность и время", callback_data="adm_view:activity")
            ],
            [
                InlineKeyboardButton(text="💬 Чаты и сообщения", callback_data="adm_view:chats"),
                InlineKeyboardButton(text="👥 Аудитория и пол", callback_data="adm_view:users")
            ],
            [
                InlineKeyboardButton(text=f"🔒 Пароль бота: {lock_status}", callback_data=toggle_cb),
                InlineKeyboardButton(text="✏️ Сменить пароль", callback_data="adm_act:set_pass")
            ],
            [
                InlineKeyboardButton(text="🤖 Виртуальные анкеты (300)", callback_data="adm_view:bots"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data="adm_view:refresh")
            ],
            [
                InlineKeyboardButton(text="🚪 Закрыть панель", callback_data="adm_act:close")
            ]
        ]
    )

def get_admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад в панель админа", callback_data="adm_view:main")]
        ]
    )

def get_bots_management_keyboard(current_rate: float = 0.20) -> InlineKeyboardMarkup:
    rate_percent = int(round(current_rate * 100))
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Создать 300 анкет", callback_data="adm_bots:seed"),
                InlineKeyboardButton(text="🗑 Очистить ботов", callback_data="adm_bots:clear")
            ],
            [
                InlineKeyboardButton(text=f"⚡ Текущий отклик на лайки: {rate_percent}%", callback_data="adm_bots:rate_info")
            ],
            [
                InlineKeyboardButton(text="10%", callback_data="adm_rate:0.10"),
                InlineKeyboardButton(text="20% (норма)", callback_data="adm_rate:0.20"),
                InlineKeyboardButton(text="30%", callback_data="adm_rate:0.30"),
                InlineKeyboardButton(text="100% (тест)", callback_data="adm_rate:1.00"),
            ],
            [
                InlineKeyboardButton(text="🔙 Назад в панель админа", callback_data="adm_view:main")
            ]
        ]
    )
