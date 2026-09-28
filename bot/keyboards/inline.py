from typing import List, Tuple
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_gender_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👨 Я парень (Мужчина)", callback_data="set_gender:male")],
            [InlineKeyboardButton(text="👩 Я девушка (Женщина)", callback_data="set_gender:female")],
            [InlineKeyboardButton(text="👥 Мы пара (М+Ж / Ж+Ж / М+М)", callback_data="set_gender:couple")]
        ]
    )

def get_target_gender_keyboard(prefix: str = "set_target") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👩 Ищу девушек", callback_data=f"{prefix}:female")],
            [InlineKeyboardButton(text="👨 Ищу мужчин", callback_data=f"{prefix}:male")],
            [InlineKeyboardButton(text="👥 Ищу пары", callback_data=f"{prefix}:couple")],
            [InlineKeyboardButton(text="🌟 Ищу всех подряд", callback_data=f"{prefix}:all")]
        ]
    )

def get_avatar_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Начать знакомства!", callback_data="avatar_confirm:keep")],
            [InlineKeyboardButton(text="🎲 Подобрать другой образ", callback_data="avatar_confirm:shuffle")],
            [InlineKeyboardButton(text="📸 Загрузить своё личное фото", callback_data="avatar_confirm:custom")]
        ]
    )

def get_persona_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Выбрать случайный образ", callback_data="persona_act:random")],
            [InlineKeyboardButton(text="🎠 Каталог всех 20 образов", callback_data="persona_nav:0")],
            [InlineKeyboardButton(text="📸 Загрузить своё личное фото", callback_data="edit:photo")],
            [InlineKeyboardButton(text="🔙 Вернуться в настройки", callback_data="edit:cancel")]
        ]
    )

def get_persona_carousel_keyboard(index: int, total: int, persona_id: str) -> InlineKeyboardMarkup:
    prev_idx = (index - 1) % total
    next_idx = (index + 1) % total
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="◀️ Назад", callback_data=f"persona_nav:{prev_idx}"),
                InlineKeyboardButton(text="✅ Выбрать", callback_data=f"persona_pick:{persona_id}"),
                InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"persona_nav:{next_idx}")
            ],
            [InlineKeyboardButton(text="🎲 Подобрать случайный", callback_data="persona_act:random")],
            [InlineKeyboardButton(text="🔙 В меню аватарок", callback_data="edit:persona_menu")]
        ]
    )

def get_discovery_keyboard(target_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like:{target_id}"),
                InlineKeyboardButton(text="💌 Написать", callback_data=f"msg:{target_id}"),
                InlineKeyboardButton(text="👎 Пропустить", callback_data=f"dislike:{target_id}")
            ],
            [
                InlineKeyboardButton(text="⚙️ Фильтры поиска", callback_data="search_filter:open"),
                InlineKeyboardButton(text="⚠️ Пожаловаться", callback_data=f"report:{target_id}")
            ]
        ]
    )

def get_search_filters_keyboard(city: str, age_min: int, age_max: int, target_gender: str) -> InlineKeyboardMarkup:
    city_str = city if city else "Любой 🌍"
    age_str = "Любой 🎂" if (age_min <= 18 and age_max >= 90) else f"{age_min}–{age_max} л."
    target_map = {"female": "Девушек 👩", "male": "Мужчин 👨", "couple": "Пары 👥", "all": "Всех 🌟"}
    target_str = target_map.get(target_gender, "Всех 🌟")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"📍 Город: {city_str}", callback_data="filter_act:city")],
            [InlineKeyboardButton(text=f"🎂 Возраст: {age_str}", callback_data="filter_act:age")],
            [InlineKeyboardButton(text=f"🎯 Кого ищем: {target_str}", callback_data="filter_act:target")],
            [InlineKeyboardButton(text="▶️ Смотреть анкеты с этими фильтрами", callback_data="filter_act:start")]
        ]
    )

def get_filter_age_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="18–25 лет", callback_data="set_f_age:18:25"),
                InlineKeyboardButton(text="22–35 лет", callback_data="set_f_age:22:35")
            ],
            [
                InlineKeyboardButton(text="30–50 лет", callback_data="set_f_age:30:50"),
                InlineKeyboardButton(text="Любой (18+)", callback_data="set_f_age:18:99")
            ],
            [InlineKeyboardButton(text="✏️ Ввести свой диапазон", callback_data="set_f_age:custom")],
            [InlineKeyboardButton(text="🔙 Назад к фильтрам", callback_data="search_filter:open")]
        ]
    )

def get_filter_city_keyboard(user_city: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"📍 Мой город: {user_city}", callback_data=f"set_f_city:{user_city}")],
            [InlineKeyboardButton(text="🌍 Любой город (вся география)", callback_data="set_f_city:all")],
            [InlineKeyboardButton(text="✏️ Ввести другой город", callback_data="set_f_city:custom")],
            [InlineKeyboardButton(text="🔙 Назад к фильтрам", callback_data="search_filter:open")]
        ]
    )

def get_match_keyboard(session_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Начать диалог прямо сейчас", callback_data=f"open_chat:{session_id}")],
            [InlineKeyboardButton(text="🔍 Продолжить поиск анкет", callback_data="resume_discovery")]
        ]
    )

def get_user_chats_keyboard(chats: list) -> InlineKeyboardMarkup:
    buttons = []
    for item in chats:
        if isinstance(item, dict):
            c_id = item["session_id"]
            name = item.get("name", "Собеседник")
            icon = item.get("gender_icon", "💬")
            num = item.get("num", "")
            prefix = f"{num}️⃣ " if num else "💬 "
            btn_text = f"{prefix}{icon} {name} — Открыть чат"
        elif isinstance(item, (tuple, list)):
            c, partner = item[0], item[1]
            c_id = c.id
            is_couple = (partner.gender == "couple")
            icon = "👥" if is_couple else ("👨" if partner.gender == "male" else "👩")
            btn_text = f"💬 {icon} {partner.first_name} — Открыть чат"
        else:
            continue
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"open_chat:{c_id}")])
    buttons.append([InlineKeyboardButton(text="🔍 Искать новые анкеты", callback_data="resume_discovery")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_in_chat_actions_keyboard(session_id: int, partner_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Посмотреть анкету и фото", callback_data=f"chat_view_profile:{partner_id}")],
            [InlineKeyboardButton(text="💬 Все мои диалоги", callback_data="chat_list_all")],
            [InlineKeyboardButton(text="🔥 Сжечь и завершить диалог", callback_data=f"ask_burn:{session_id}")]
        ]
    )

def get_confirm_burn_keyboard(session_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Да, навсегда сжечь переписку", callback_data=f"confirm_burn:{session_id}")],
            [InlineKeyboardButton(text="❌ Отмена, продолжить общение", callback_data=f"cancel_burn:{session_id}")]
        ]
    )

def get_incoming_like_alert_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💌 Посмотреть симпатии", callback_data="show_likes_list")],
            [InlineKeyboardButton(text="🔍 Продолжить поиск", callback_data="resume_discovery")]
        ]
    )

def get_new_message_alert_keyboard(session_id: int, partner_name: str = "") -> InlineKeyboardMarkup:
    label = f"💬 Открыть диалог с {partner_name}" if partner_name else "💬 Открыть диалог"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"open_chat:{session_id}")],
            [InlineKeyboardButton(text="💬 Все мои диалоги", callback_data="chat_list_all")]
        ]
    )

def get_secret_timer_keyboard(secret_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏱ 15 сек", callback_data=f"set_sec_timer:{secret_id}:15"),
                InlineKeyboardButton(text="⏱ 30 сек", callback_data=f"set_sec_timer:{secret_id}:30")
            ],
            [
                InlineKeyboardButton(text="⏱ 45 сек", callback_data=f"set_sec_timer:{secret_id}:45"),
                InlineKeyboardButton(text="⏱ 60 сек", callback_data=f"set_sec_timer:{secret_id}:60")
            ],
            [
                InlineKeyboardButton(text="📷 Обычное фото", callback_data=f"set_sec_timer:{secret_id}:0"),
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"set_sec_timer:cancel")
            ]
        ]
    )

def get_view_secret_keyboard(secret_id: int, duration: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"👁 Открыть фото ({duration} сек)", callback_data=f"view_secret:{secret_id}")]
        ]
    )

def get_incoming_like_keyboard(from_user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❤️ Ответить взаимной симпатией", callback_data=f"like:{from_user_id}")],
            [InlineKeyboardButton(text="👎 Пропустить анкету", callback_data=f"dislike:{from_user_id}")]
        ]
    )

def get_settings_keyboard(is_active: bool, is_couple: bool = False, has_password: bool = False) -> InlineKeyboardMarkup:
    status_btn = "⏸ Поставить поиск на паузу" if is_active else "▶️ Возобновить поиск анкет"
    status_cb = "toggle_active:0" if is_active else "toggle_active:1"

    target_btn = "🎯 Кого ищем" if is_couple else "🎯 Кого ищу"
    bio_btn = "📝 О паре" if is_couple else "📝 О себе"
    age_btn = "🎂 Возраст пары" if is_couple else "🎂 Возраст"
    name_btn = "✏️ Имя пары" if is_couple else "✏️ Имя"
    persona_btn = "🎭 Образ пары" if is_couple else "🎭 Сменить образ"
    pass_btn = "🔒 Пароль: ВКЛ" if has_password else "🔓 Пароль: ВЫКЛ"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=persona_btn, callback_data="edit:persona_menu"),
                InlineKeyboardButton(text="📸 Своё фото", callback_data="edit:photo")
            ],
            [
                InlineKeyboardButton(text=name_btn, callback_data="edit:name"),
                InlineKeyboardButton(text=age_btn, callback_data="edit:age")
            ],
            [
                InlineKeyboardButton(text=bio_btn, callback_data="edit:bio"),
                InlineKeyboardButton(text="📍 Город", callback_data="edit:city")
            ],
            [
                InlineKeyboardButton(text=target_btn, callback_data="edit:target"),
                InlineKeyboardButton(text="⚙️ Фильтры", callback_data="search_filter:open")
            ],
            [
                InlineKeyboardButton(text=pass_btn, callback_data="personal_pass:menu"),
                InlineKeyboardButton(text=status_btn, callback_data=status_cb)
            ],
            [InlineKeyboardButton(text="🎁 Пригласить друга (+бонус)", callback_data="ref:share")],
            [InlineKeyboardButton(text="🔄 Заполнить анкету заново", callback_data="edit:restart")],
            [InlineKeyboardButton(text="🗑 Удалить анкету", callback_data="delete_profile:ask")]
        ]
    )

def get_share_referral_keyboard(user_tg_id: int) -> InlineKeyboardMarkup:
    share_url = f"https://t.me/share/url?url=https://t.me/pure_match_bot?start=ref_{user_tg_id}&text=%D0%9F%D1%80%D0%B8%D0%B2%D0%B5%D1%82!%20%D0%97%D0%B0%D1%85%D0%BE%D0%B4%D0%B8%20%D0%B2%20%D0%B0%D0%BD%D0%BE%D0%BD%D0%B8%D0%BC%D0%BD%D1%8B%D0%B5%20%D0%B7%D0%BD%D0%B0%D0%BA%D0%BE%D0%BC%D1%81%D1%82%D0%B2%D0%B0%20Pure%20%F0%9F%94%A5"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Отправить ссылку друзьям", url=share_url)],
            [InlineKeyboardButton(text="🔙 Назад в настройки", callback_data="edit:cancel")]
        ]
    )


def get_personal_password_keyboard(has_password: bool) -> InlineKeyboardMarkup:
    if has_password:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="✏️ Сменить пароль", callback_data="personal_pass:set")],
                [InlineKeyboardButton(text="🔓 Снять пароль", callback_data="personal_pass:remove")],
                [InlineKeyboardButton(text="🔒 Заблокировать экран сейчас", callback_data="personal_pass:lock_now")],
                [InlineKeyboardButton(text="🔙 Назад в настройки", callback_data="edit:cancel")]
            ]
        )
    else:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔒 Установить личный пароль", callback_data="personal_pass:set")],
                [InlineKeyboardButton(text="🔙 Назад в настройки", callback_data="edit:cancel")]
            ]
        )

def get_delete_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Да, удалить анкету навсегда", callback_data="delete_profile:confirm")],
            [InlineKeyboardButton(text="❌ Отмена, остаться в сервисе", callback_data="delete_profile:cancel")]
        ]
    )
