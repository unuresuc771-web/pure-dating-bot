import os
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from bot.database.db import async_session_maker
from bot.database.models import get_random_default_avatar
from bot.services.user_service import UserService
from bot.services.matching import MatchingService
import html
from bot.keyboards.inline import (
    get_settings_keyboard,
    get_target_gender_keyboard,
    get_incoming_like_keyboard,
    get_persona_menu_keyboard,
    get_persona_carousel_keyboard,
    get_delete_profile_keyboard,
    get_personal_password_keyboard,
    get_share_referral_keyboard
)
from bot.keyboards.reply import get_main_keyboard, get_cancel_keyboard
from bot.states.profile import EditProfileStates, PersonalPasswordStates
from bot.middlewares.access_gate import AccessGateMiddleware
from bot.constants import get_random_pure_nickname
from bot.services.persona_service import (
    get_random_persona,
    get_personas_by_gender,
    get_persona_by_id,
    get_persona_by_name,
    get_persona_by_avatar
)
from bot.services.avatar_cache import AvatarCacheService
from bot.handlers.registration import start_simple_registration

logger = logging.getLogger(__name__)
router = Router(name="simple_profile")

async def send_user_photo(target_chat_id: int, bot: Bot, user, caption: str, keyboard=None):
    try:
        await AvatarCacheService.send_avatar_photo(
            bot=bot,
            chat_id=target_chat_id,
            avatar_path=user.avatar_path,
            is_custom_photo=user.is_custom_photo,
            caption=caption,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Failed to send profile photo: {e}")
        await bot.send_message(chat_id=target_chat_id, text=caption, reply_markup=keyboard, parse_mode="HTML")

@router.message(F.text.in_({"👤 Профиль", "👤 Моя анкета"}))
async def show_my_profile(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала создайте анкету через /start.")
            return

        if user.active_chat_id:
            await UserService.set_active_chat(session, user.id, None)

        caption = UserService.format_caption(user, is_owner=True)
        is_couple = (user.gender == "couple")
        keyboard = get_settings_keyboard(user.is_active, is_couple=is_couple, has_password=bool(user.personal_password))
        await send_user_photo(message.from_user.id, bot, user, caption, keyboard)

@router.message(F.text.in_({"💌 Симпатии", "💌 Кому я нравлюсь"}))
async def show_incoming_likes(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала создайте анкету через /start.")
            return

        if user.active_chat_id:
            await UserService.set_active_chat(session, user.id, None)

        incoming = await MatchingService.get_incoming_likes(session, user.id)
        if not incoming:
            await message.answer(
                "💌 <b>Новых симпатий пока нет.</b>\nПродолжайте поиск в «🔍 Поиск»!",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            return

        await message.answer(f"💌 <b>Вам поставили лайк ({len(incoming)} чел.):</b>", parse_mode="HTML")
        for sender, compliment in incoming[:3]:  # Показываем до 3 за раз
            cap = UserService.format_caption(sender, is_owner=False)
            if compliment:
                cap = f"💌 <b>Сообщение:</b> <i>«{compliment}»</i>\n\n" + cap
            await send_user_photo(
                message.from_user.id,
                bot,
                sender,
                cap,
                get_incoming_like_keyboard(sender.id)
            )

@router.message(F.text == "⚙️ Настройки")
async def show_settings_menu(message: Message):
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if not user:
            return

        status_text = "🟢 Видна в поиске" if user.is_active else "⏸ На паузе (скрыта)"
        target_map = {"female": "девушек 👩", "male": "парней 👨", "couple": "пары 👥", "all": "всех 👥"}
        target_label = target_map.get(user.target_gender, user.target_gender)
        is_couple = (user.gender == "couple")

        target_prompt = "• Кого ищете" if is_couple else "• Кого ищешь"
        title_settings = "⚙️ <b>Настройки профиля пары:</b>\n\n" if is_couple else "⚙️ <b>Настройки профиля:</b>\n\n"

        text = (
            f"{title_settings}"
            f"• Статус видимости: {status_text}\n"
            f"• Город: <b>{user.city}</b>\n"
            f"{target_prompt}: <b>{target_label}</b>\n\n"
            "Выберите, что хотите изменить:"
        )
        await message.answer(text, reply_markup=get_settings_keyboard(user.is_active, is_couple=is_couple, has_password=bool(user.personal_password)), parse_mode="HTML")

@router.callback_query(F.data.startswith("toggle_active:"))
async def cb_toggle_active(call: CallbackQuery):
    new_active = call.data.split(":")[1] == "1"
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        if user:
            await UserService.set_active(session, user.id, new_active)
            is_couple = (user.gender == "couple")
            await call.message.edit_reply_markup(reply_markup=get_settings_keyboard(new_active, is_couple=is_couple, has_password=bool(user.personal_password)))
            status_word = "активирована" if new_active else "приостановлена"
            await call.answer(f"Анкета {status_word}!")

@router.callback_query(F.data == "edit:persona_menu")
async def cb_edit_persona_menu(call: CallbackQuery):
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        if not user:
            return
        cur_text = f"Текущий образ: <b>«{user.first_name}»</b>" if not user.is_custom_photo else "Текущее фото: <b>Личное фото</b>"
        await call.message.answer(
            f"🎭 <b>Управление анонимным образом</b>\n\n"
            f"{cur_text}\n\n"
            f"Каждому аватару соответствует своё имя. Выберите действие:",
            reply_markup=get_persona_menu_keyboard(),
            parse_mode="HTML"
        )
        await call.answer()

@router.callback_query(F.data == "persona_act:random")
async def cb_persona_act_random(call: CallbackQuery):
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        if not user:
            return
        new_persona = get_random_persona(user.gender, exclude_name=user.first_name)
        await UserService.update_user(
            session,
            user.id,
            first_name=new_persona.name,
            avatar_path=new_persona.avatar_path,
            is_custom_photo=False
        )
        caption = (
            f"🎉 <b>Ваш новый образ активирован!</b>\n\n"
            f"👤 Псевдоним: <b>{new_persona.name}</b>\n"
            f"🎨 <i>Узор: {new_persona.pattern}</i>\n"
            f"🌈 <i>Палитра: {new_persona.palette_name}</i>"
        )
        await call.message.answer_photo(
            photo=FSInputFile(new_persona.avatar_path),
            caption=caption,
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        await call.answer("Образ успешно изменён!")

@router.callback_query(F.data.startswith("persona_nav:"))
async def cb_persona_nav(call: CallbackQuery):
    idx = int(call.data.split(":")[1])
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        if not user:
            return
        personas = get_personas_by_gender(user.gender)
        total = len(personas)
        idx = idx % total
        p = personas[idx]

        caption = (
            f"🎭 <b>Каталог образов [{idx + 1}/{total}]</b>\n\n"
            f"👤 Имя: <b>«{p.name}»</b>\n"
            f"🌀 Узор фона: <i>{p.pattern}</i>\n"
            f"🎨 Палитра: <i>{p.palette_name}</i>"
        )
        markup = get_persona_carousel_keyboard(idx, total, p.id)

        try:
            from aiogram.types import InputMediaPhoto
            await call.message.edit_media(
                media=InputMediaPhoto(media=FSInputFile(p.avatar_path), caption=caption, parse_mode="HTML"),
                reply_markup=markup
            )
        except Exception:
            await call.message.delete()
            await call.message.answer_photo(
                photo=FSInputFile(p.avatar_path),
                caption=caption,
                reply_markup=markup,
                parse_mode="HTML"
            )
        await call.answer()

@router.callback_query(F.data.startswith("persona_pick:"))
async def cb_persona_pick(call: CallbackQuery):
    p_id = call.data.split(":")[1]
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        if not user:
            return
        persona = get_persona_by_id(p_id)
        if not persona:
            await call.answer("Образ не найден", show_alert=True)
            return

        await UserService.update_user(
            session,
            user.id,
            first_name=persona.name,
            avatar_path=persona.avatar_path,
            is_custom_photo=False
        )
        await call.message.delete()
        await call.message.answer_photo(
            photo=FSInputFile(persona.avatar_path),
            caption=f"✅ Отличный выбор! Ваш профиль обновлен на образ <b>«{persona.name}»</b>!",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        await call.answer("Образ применён!")

@router.callback_query(F.data == "edit:cancel")
async def cb_edit_cancel(call: CallbackQuery):
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        is_active = user.is_active if user else True
        is_couple = (user.gender == "couple") if user else False
        try:
            await call.message.delete()
        except Exception:
            pass
        title = "⚙️ <b>Настройки профиля пары:</b>" if is_couple else "⚙️ <b>Настройки анкеты:</b>"
        has_password = bool(user.personal_password if user else False)
        await call.message.answer(title, reply_markup=get_settings_keyboard(is_active, is_couple=is_couple, has_password=has_password), parse_mode="HTML")
        await call.answer()

@router.callback_query(F.data == "edit:photo")
async def cb_edit_photo(call: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfileStates.photo)
    await call.message.reply(
        "📸 Отправьте личное фото для анкеты (или напишите <b>«аватар»</b>, чтобы выбрать случайный графический образ):\n"
        "<i>(Или нажмите «❌ Отмена»)</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()

@router.message(EditProfileStates.photo, F.photo)
async def process_edit_custom_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.clear()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if user:
            await UserService.update_user(session, user.id, avatar_path=photo_id, is_custom_photo=True)
            await message.answer("✅ Фотография успешно обновлена!", reply_markup=get_main_keyboard())

@router.message(EditProfileStates.photo, F.text.lower().in_(["аватар", "заставка", "рандом"]))
async def process_edit_shuffle_avatar(message: Message, state: FSMContext):
    await state.clear()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if user:
            new_persona = get_random_persona(user.gender, exclude_name=user.first_name)
            await UserService.update_user(
                session,
                user.id,
                first_name=new_persona.name,
                avatar_path=new_persona.avatar_path,
                is_custom_photo=False
            )
            await message.answer_photo(
                photo=FSInputFile(new_persona.avatar_path),
                caption=f"✅ Анонимный образ обновлен на <b>«{new_persona.name}»</b>!",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )

@router.callback_query(F.data == "edit:name")
async def cb_edit_name(call: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfileStates.name)
    await call.message.reply(
        "🎭 Введите новое имя/псевдоним (или напишите <b>«рандом»</b> для выбора нового анонимного образа):\n"
        "<i>(Или нажмите «❌ Отмена»)</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()

@router.message(EditProfileStates.name, F.text)
async def process_edit_name(message: Message, state: FSMContext):
    input_text = message.text.strip()
    await state.clear()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if not user:
            return

        if input_text.lower() in ["рандом", "случайно", "псевдоним"]:
            new_persona = get_random_persona(user.gender, exclude_name=user.first_name)
            await UserService.update_user(
                session,
                user.id,
                first_name=new_persona.name,
                avatar_path=new_persona.avatar_path,
                is_custom_photo=False
            )
            await message.answer_photo(
                photo=FSInputFile(new_persona.avatar_path),
                caption=f"✅ Выбран новый образ <b>«{new_persona.name}»</b>!",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            return

        matching_persona = get_persona_by_name(input_text, user.gender)
        if matching_persona:
            await UserService.update_user(
                session,
                user.id,
                first_name=matching_persona.name,
                avatar_path=matching_persona.avatar_path,
                is_custom_photo=False
            )
            await message.answer_photo(
                photo=FSInputFile(matching_persona.avatar_path),
                caption=f"✅ Установлен анонимный образ <b>«{matching_persona.name}»</b> с соответствующей заставкой!",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            return

        if len(input_text) < 2 or len(input_text) > 30:
            await message.answer("⚠️ Имя должно быть от 2 до 30 символов. Попробуйте еще раз:")
            return

        await UserService.update_user(session, user.id, first_name=input_text)
        await message.answer(f"✅ Имя/псевдоним обновлен на <b>{input_text}</b>!", reply_markup=get_main_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "edit:bio")
async def cb_edit_bio(call: CallbackQuery, state: FSMContext):
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        is_couple = (user.gender == "couple") if user else False
        prompt = "✏️ Напишите новое описание для вашей пары:\n<i>(Или нажмите «❌ Отмена»)</i>" if is_couple else "✏️ Напишите новый текст «О себе»:\n<i>(Или нажмите «❌ Отмена»)</i>"
        await state.set_state(EditProfileStates.bio)
        await call.message.reply(prompt, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
        await call.answer()

@router.message(EditProfileStates.bio, F.text)
async def process_edit_bio(message: Message, state: FSMContext):
    bio_text = message.text.strip()
    await state.clear()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if user:
            is_couple = (user.gender == "couple")
            await UserService.update_user(session, user.id, bio=bio_text)
            msg = "✅ Описание пары успешно обновлено!" if is_couple else "✅ Текст «О себе» успешно обновлен!"
            await message.answer(msg, reply_markup=get_main_keyboard())

@router.callback_query(F.data == "edit:age")
async def cb_edit_age(call: CallbackQuery, state: FSMContext):
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        if not user:
            return
        is_couple = (user.gender == "couple")
        if is_couple:
            prompt = (
                "🎂 Укажите возраст обоих партнеров (например: <b>28/25</b> или <b>30 и 27</b>):\n"
                "<i>(Или нажмите «❌ Отмена»)</i>"
            )
        else:
            prompt = (
                "🎂 Укажите ваш возраст (числом от 16 до 99):\n"
                "<i>(Или нажмите «❌ Отмена»)</i>"
            )
        await state.set_state(EditProfileStates.age)
        await call.message.reply(prompt, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
        await call.answer()

@router.message(EditProfileStates.age, F.text)
async def process_edit_age(message: Message, state: FSMContext):
    import re
    raw_text = message.text.strip()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if not user:
            await state.clear()
            return

        is_couple = (user.gender == "couple")
        numbers = [int(n) for n in re.findall(r'\b\d+\b', raw_text)]
        valid_numbers = [n for n in numbers if 16 <= n <= 99]

        if is_couple:
            if len(valid_numbers) >= 2:
                a1, a2 = valid_numbers[0], valid_numbers[1]
                age = round((a1 + a2) / 2)
                couple_age = f"{a1}/{a2}"
            elif len(valid_numbers) == 1:
                age = valid_numbers[0]
                couple_age = str(age)
            else:
                await message.answer("⚠️ Введите возраст обоих партнеров (например: <b>28/25</b>):", parse_mode="HTML")
                return
            await UserService.update_user(session, user.id, age=age, couple_age=couple_age)
            await state.clear()
            await message.answer(f"✅ Возраст пары обновлен на <b>{couple_age}</b>!", reply_markup=get_main_keyboard(), parse_mode="HTML")
        else:
            if not valid_numbers:
                await message.answer("⚠️ Введите возраст числом (от 16 до 99):")
                return
            age = valid_numbers[0]
            await UserService.update_user(session, user.id, age=age, couple_age=None)
            await state.clear()
            await message.answer(f"✅ Возраст обновлен на <b>{age}</b>!", reply_markup=get_main_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "edit:city")
async def cb_edit_city(call: CallbackQuery, state: FSMContext):
    await state.set_state(EditProfileStates.city)
    await call.message.reply(
        "📍 Напишите название вашего города:\n<i>(Или нажмите «❌ Отмена»)</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()

@router.message(EditProfileStates.city, F.text)
async def process_edit_city(message: Message, state: FSMContext):
    city = message.text.strip().title()
    await state.clear()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if user:
            await UserService.update_user(session, user.id, city=city)
            await message.answer(f"✅ Город обновлен на <b>{city}</b>!", reply_markup=get_main_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "edit:target")
async def cb_edit_target(call: CallbackQuery):
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        is_couple = (user.gender == "couple") if user else False
        prompt = "🎯 Кого вы хотите искать?" if is_couple else "🎯 Кого ты хочешь искать?"
        await call.message.reply(prompt, reply_markup=get_target_gender_keyboard(prefix="edit_t"))
        await call.answer()

@router.callback_query(F.data.startswith("edit_t:"))
async def process_edit_target_gender(call: CallbackQuery):
    target = call.data.split(":")[1]
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        if user:
            await UserService.update_user(session, user.id, target_gender=target)
            target_map = {"female": "девушек 👩", "male": "мужчин 👨", "couple": "пары 👥", "all": "всех 🌟"}
            await call.message.delete_reply_markup()
            await call.message.answer(
                f"✅ Теперь вы ищете: <b>{target_map.get(target, target)}</b>",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
    await call.answer()

@router.callback_query(F.data == "edit:restart")
async def cb_restart_profile(call: CallbackQuery, state: FSMContext):
    await call.message.delete_reply_markup()
    await start_simple_registration(call.message, state)
    await call.answer()

@router.callback_query(F.data == "delete_profile:ask")
async def cb_ask_delete_profile(call: CallbackQuery):
    await call.answer()
    text = (
        "⚠️ <b>Удаление анкеты навсегда</b>\n\n"
        "Вы действительно хотите удалить свой профиль?\n\n"
        "• Все ваши данные будут стерты без следа\n"
        "• Все активные чаты, переписки и фото будут сожжены у обоих собеседников\n"
        "• Восстановить анкету будет невозможно\n\n"
        "Вы уверены?"
    )
    try:
        await call.message.edit_text(text, reply_markup=get_delete_profile_keyboard(), parse_mode="HTML")
    except Exception:
        await call.message.answer(text, reply_markup=get_delete_profile_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "delete_profile:cancel")
async def cb_cancel_delete_profile(call: CallbackQuery):
    await call.answer("👌 Удаление отменено.")
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        if user:
            caption = UserService.format_caption(user, is_owner=True)
            kb = get_settings_keyboard(user.is_active, is_couple=(user.gender == "couple"), has_password=bool(user.personal_password))
            try:
                await call.message.edit_text(caption, reply_markup=kb, parse_mode="HTML")
            except Exception:
                await call.message.answer(caption, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "delete_profile:confirm")
async def cb_confirm_delete_profile(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    await state.clear()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        if user:
            await UserService.delete_user_completely(bot, session, user.id)

    try:
        await call.message.delete()
    except Exception:
        pass

    from aiogram.types import ReplyKeyboardRemove
    await call.message.answer(
        "🗑 <b>Ваша анкета полностью удалена.</b>\n\n"
        "Все переписки, фотографии, лайки и следы стёрты навсегда.\n\n"
        "Если захотите создать новый профиль — отправьте команду /start.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

# =====================================================================
# ПЕРСОНАЛЬНЫЙ ПАРОЛЬ (PIN) ДЛЯ КАЖДОГО ПОЛЬЗОВАТЕЛЯ
# =====================================================================

@router.callback_query(F.data == "personal_pass:menu")
async def cb_personal_pass_menu(call: CallbackQuery):
    await call.answer()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        if not user:
            return
        has_pass = bool(user.personal_password)
        status_text = "🟢 Установлен (вход защищен)" if has_pass else "🔴 Не установлен (вход свободный)"
        text = (
            "🔒 <b>Личный пароль доступа (PIN)</b>\n\n"
            f"• Статус защиты: <b>{status_text}</b>\n\n"
            "Вы можете установить персональный PIN-код или пароль (от 4 до 20 символов), "
            "чтобы скрыть анкету и переписки от посторонних глаз на вашем устройстве.\n\n"
            "<i>Если пароль не нужен, вход в бот остаётся абсолютно свободным.</i>"
        )
        try:
            await call.message.edit_text(text, reply_markup=get_personal_password_keyboard(has_pass), parse_mode="HTML")
        except Exception:
            await call.message.answer(text, reply_markup=get_personal_password_keyboard(has_pass), parse_mode="HTML")

@router.callback_query(F.data == "personal_pass:set")
async def cb_personal_pass_set(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(PersonalPasswordStates.setting_new_password)
    await call.message.answer(
        "✏️ <b>Установка личного пароля</b>\n\n"
        "Напишите в ответ желаемый PIN-код (например, <code>1234</code>) или пароль (от 4 до 20 символов):\n\n"
        "<i>(Или отправьте /cancel для отмены)</i>",
        parse_mode="HTML"
    )

@router.message(PersonalPasswordStates.setting_new_password, F.text)
async def process_new_personal_password(message: Message, state: FSMContext):
    pwd = message.text.strip()
    if pwd.startswith("/cancel"):
        await state.clear()
        await message.answer("❌ Установка пароля отменена.", reply_markup=get_main_keyboard())
        return
    if len(pwd) < 4 or len(pwd) > 20:
        await message.answer("⚠️ Пароль должен быть длиной от 4 до 20 символов. Попробуйте еще раз:")
        return

    await state.clear()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if user:
            await UserService.set_personal_password(session, user.id, pwd)
            AccessGateMiddleware.unlock_user(message.from_user.id)
            await message.answer(
                f"✅ <b>Личный пароль успешно установлен!</b>\n\n"
                f"Ваш пароль: <code>{html.escape(pwd)}</code>\n\n"
                "Теперь при блокировке сессии доступ будет защищён этим паролем.\n"
                "Вы можете заблокировать сессию в любой момент кнопкой «🔒 Заблокировать» или командой /lock.",
                reply_markup=get_main_keyboard(has_lock=True),
                parse_mode="HTML"
            )

@router.callback_query(F.data == "personal_pass:remove")
async def cb_personal_pass_remove(call: CallbackQuery):
    await call.answer()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        if user:
            await UserService.remove_personal_password(session, user.id)
            AccessGateMiddleware.unlock_user(call.from_user.id)
            await call.message.answer(
                "🔓 <b>Личный пароль успешно удалён!</b>\n\n"
                "Теперь вход в бот абсолютно свободный без ввода пароля.",
                reply_markup=get_main_keyboard(has_lock=False),
                parse_mode="HTML"
            )

@router.callback_query(F.data == "personal_pass:lock_now")
async def cb_personal_pass_lock(call: CallbackQuery):
    AccessGateMiddleware.lock_user(call.from_user.id)
    await call.answer("🔒 Сессия заблокирована!", show_alert=True)
    await call.message.answer(
        "🔒 <b>Сессия заблокирована!</b>\n\n"
        "Для продолжения введите ваш личный пароль в чат:",
        parse_mode="HTML"
    )

@router.message(F.text.in_({"/lock", "🔒 Заблокировать"}))
async def cmd_lock(message: Message):
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if not user or not user.personal_password:
            await message.answer(
                "ℹ️ У вас пока не установлен личный пароль.\n\n"
                "Вы можете установить его в меню «Настройки» -> «🔒 Пароль: ВЫКЛ».",
                reply_markup=get_main_keyboard(has_lock=False)
            )
            return

        AccessGateMiddleware.lock_user(message.from_user.id)
        await message.answer(
            "🔒 <b>Сессия заблокирована!</b>\n\n"
            "Для входа введите ваш личный пароль в чат:",
            parse_mode="HTML"
        )

@router.callback_query(F.data == "ref:share")
async def cb_referral_share(call: CallbackQuery):
    await call.answer()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        if not user:
            return
        link = f"https://t.me/pure_match_bot?start=ref_{user.telegram_id}"
        count = user.referral_count or 0
        text = (
            "🎁 <b>Партнёрская программа Pure Match</b>\n\n"
            f"🔗 Ваша личная ссылка для приглашений:\n"
            f"<code>{link}</code>\n\n"
            f"👥 Вы пригласили: <b>{count} чел.</b>\n\n"
            "🔥 <b>Бонусы за приглашения:</b>\n"
            "• Ваша анкета поднимается в самый верх ленты поиска.\n"
            "• Больше просмотров, лайков и взаимных совпадений!\n\n"
            "<i>Нажмите кнопку ниже, чтобы переслать ссылку в чаты или друзьям:</i>"
        )
        await call.message.answer(text, reply_markup=get_share_referral_keyboard(user.telegram_id), parse_mode="HTML")



