import re
import html
import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.database.db import async_session_maker
from bot.database.models import get_random_default_avatar
from bot.services.user_service import UserService
from bot.services.persona_service import get_random_persona, get_persona_by_name
from bot.services.avatar_cache import AvatarCacheService
from bot.states.profile import RegistrationStates
from bot.keyboards.inline import (
    get_gender_keyboard,
    get_target_gender_keyboard,
    get_avatar_choice_keyboard
)
from bot.keyboards.reply import get_main_keyboard, get_cancel_keyboard, get_skip_keyboard

router = Router(name="simple_registration")

async def start_simple_registration(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(RegistrationStates.gender)
    suggested_name = message.from_user.first_name or "Гость"
    await state.update_data(first_name=suggested_name)

    safe_name = html.escape(suggested_name)
    text = (
        f"👋 Привет, <b>{safe_name}</b>!\n\n"
        "Кто регистрирует анкету?"
    )
    sent = await message.answer(text, reply_markup=get_gender_keyboard(), parse_mode="HTML")
    await state.update_data(last_q_id=sent.message_id)

@router.callback_query(RegistrationStates.gender, F.data.startswith("set_gender:"))
async def process_gender(call: CallbackQuery, state: FSMContext):
    await call.answer()
    gender = call.data.split(":")[1]
    persona = get_random_persona(gender)
    await state.update_data(
        gender=gender,
        first_name=persona.name,
        avatar_path=persona.avatar_path,
        persona_id=persona.id,
        is_custom_photo=False
    )

    if gender == "couple":
        gender_display = "Анкета: <b>Пара 👥</b>"
        q_target = "Кого вы ищете?"
    elif gender == "male":
        gender_display = "Пол: <b>Парень 👨</b>"
        q_target = "Кого ищешь?"
    else:
        gender_display = "Пол: <b>Девушка 👩</b>"
        q_target = "Кого ищешь?"

    try:
        await call.message.edit_text(gender_display, parse_mode="HTML")
    except Exception:
        pass

    sent = await call.message.answer(q_target, reply_markup=get_target_gender_keyboard(), parse_mode="HTML")
    await state.update_data(last_q_id=sent.message_id)
    await state.set_state(RegistrationStates.target_gender)

@router.callback_query(RegistrationStates.target_gender, F.data.startswith("set_target:"))
async def process_target_gender(call: CallbackQuery, state: FSMContext):
    await call.answer()
    target = call.data.split(":")[1]
    await state.update_data(target_gender=target)
    target_map = {"female": "Девушек 👩", "male": "Мужчин 👨", "couple": "Пары 👥", "all": "Всех 🌟"}
    target_label = target_map.get(target, target)

    data = await state.get_data()
    is_couple = (data.get("gender") == "couple")

    if is_couple:
        target_display = f"Ищете: <b>{target_label}</b>"
        age_q = "Сколько вам лет? Укажите возраст обоих партнеров (например: <b>28/25</b> или <b>30 и 27</b>):"
    else:
        target_display = f"Ищешь: <b>{target_label}</b>"
        age_q = "Сколько тебе лет?"

    try:
        await call.message.edit_text(target_display, parse_mode="HTML")
    except Exception:
        pass

    sent = await call.message.answer(
        age_q,
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.update_data(last_q_id=sent.message_id)
    await state.set_state(RegistrationStates.age)

@router.message(RegistrationStates.age, F.text)
async def process_age(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    is_couple = (data.get("gender") == "couple")
    raw_text = message.text.strip()

    numbers = [int(n) for n in re.findall(r'\b\d+\b', raw_text)]
    valid_numbers = [n for n in numbers if 16 <= n <= 99]

    if is_couple:
        if len(valid_numbers) >= 2:
            a1, a2 = valid_numbers[0], valid_numbers[1]
            age = round((a1 + a2) / 2)
            couple_age = f"{a1}/{a2}"
        elif len(valid_numbers) == 1:
            if not data.get("couple_age_warned"):
                await state.update_data(couple_age_warned=True)
                await message.answer(
                    "⚠️ Для пары укажите возраст обоих партнеров через слэш или союз «и» (например: <b>28/25</b> или <b>30 и 27</b>):",
                    parse_mode="HTML"
                )
                return
            else:
                age = valid_numbers[0]
                couple_age = str(age)
        else:
            await message.answer(
                "⚠️ Укажите возраст числом от 16 до 99 (для пары двух партнеров, например: <b>28/25</b>):",
                parse_mode="HTML"
            )
            return

        await state.update_data(age=age, couple_age=couple_age)
        display_age_str = couple_age
        age_prefix = "Возраст пары:"
        city_q = "Ваш город?"
    else:
        if not valid_numbers:
            await message.answer("⚠️ Введи возраст числом (от 16 до 99):")
            return
        age = valid_numbers[0]
        await state.update_data(age=age, couple_age=None)
        display_age_str = str(age)
        age_prefix = "Возраст:"
        city_q = "Твой город?"

    last_q_id = data.get("last_q_id")

    # Чистим вопрос и ответ
    try:
        await bot.delete_message(message.chat.id, message.message_id)
        if last_q_id:
            await bot.delete_message(message.chat.id, last_q_id)
    except Exception:
        pass

    await message.answer(f"{age_prefix} <b>{display_age_str}</b>", parse_mode="HTML")
    sent = await message.answer(
        city_q,
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.update_data(last_q_id=sent.message_id)
    await state.set_state(RegistrationStates.city)

@router.message(RegistrationStates.city, F.text)
async def process_city(message: Message, state: FSMContext, bot: Bot):
    city = message.text.strip().title()
    if len(city) < 2 or len(city) > 50:
        await message.answer("⚠️ Введи корректное название города:")
        return

    await state.update_data(city=city)
    data = await state.get_data()
    is_couple = (data.get("gender") == "couple")
    last_q_id = data.get("last_q_id")

    try:
        await bot.delete_message(message.chat.id, message.message_id)
        if last_q_id:
            await bot.delete_message(message.chat.id, last_q_id)
    except Exception:
        pass

    await message.answer(f"Город: <b>{city}</b>", parse_mode="HTML")
    bio_q = "Пара слов о вашей паре или цель знакомства:" if is_couple else "Пара слов о себе или цель знакомства:"
    sent = await message.answer(
        bio_q,
        reply_markup=get_skip_keyboard(),
        parse_mode="HTML"
    )
    await state.update_data(last_q_id=sent.message_id)
    await state.set_state(RegistrationStates.bio)

@router.message(RegistrationStates.bio, F.text)
async def process_bio(message: Message, state: FSMContext, bot: Bot):
    raw_text = message.text.strip()
    bio_text = "" if raw_text in ("⏩ Пропустить", "Пропустить") else raw_text
    await state.update_data(bio=bio_text)

    data = await state.get_data()
    is_couple = (data.get("gender") == "couple")
    last_q_id = data.get("last_q_id")

    try:
        await bot.delete_message(message.chat.id, message.message_id)
        if last_q_id:
            await bot.delete_message(message.chat.id, last_q_id)
    except Exception:
        pass

    if bio_text:
        bio_prefix = "О паре:" if is_couple else "О себе:"
        await message.answer(f"{bio_prefix} <i>{bio_text}</i>", parse_mode="HTML")

    avatar_file = data.get("avatar_path")
    first_name = data.get("first_name")
    age = data.get("age")
    couple_age = data.get("couple_age")
    city = data.get("city")
    display_age = couple_age if (is_couple and couple_age) else str(age)

    if not avatar_file or not first_name:
        persona = get_random_persona(data["gender"])
        avatar_file = persona.avatar_path
        first_name = persona.name
        await state.update_data(avatar_path=avatar_file, first_name=first_name, persona_id=persona.id, is_custom_photo=False)

    header = "🎭 <b>Ваш тайный образ:</b>\n\n" if is_couple else "🎭 <b>Твой тайный образ:</b>\n\n"
    icon = "👥" if is_couple else "👤"

    caption = (
        f"{header}"
        f"{icon} <b>{first_name}</b>, {display_age}\n"
        f"📍 {city}\n"
        f"{('📝 <i>' + bio_text + '</i>') if bio_text else ''}"
    )

    await state.set_state(RegistrationStates.avatar_choice)
    await AvatarCacheService.send_avatar_photo(
        bot=bot,
        chat_id=message.chat.id,
        avatar_path=avatar_file,
        is_custom_photo=data.get("is_custom_photo", False),
        caption=caption,
        reply_markup=get_avatar_choice_keyboard()
    )

@router.callback_query(RegistrationStates.avatar_choice, F.data == "avatar_confirm:shuffle")
async def process_avatar_shuffle(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    data = await state.get_data()
    is_couple = (data.get("gender") == "couple")
    current_name = data.get("first_name")
    new_persona = get_random_persona(data["gender"], exclude_name=current_name)
    await state.update_data(
        avatar_path=new_persona.avatar_path,
        first_name=new_persona.name,
        persona_id=new_persona.id,
        is_custom_photo=False
    )

    bio_text = data.get("bio", "")
    couple_age = data.get("couple_age")
    display_age = couple_age if (is_couple and couple_age) else str(data['age'])
    header = "🎭 <b>Ваш тайный образ:</b>\n\n" if is_couple else "🎭 <b>Твой тайный образ:</b>\n\n"
    icon = "👥" if is_couple else "👤"

    caption = (
        f"{header}"
        f"{icon} <b>{new_persona.name}</b>, {display_age}\n"
        f"📍 {data['city']}\n"
        f"{('📝 <i>' + bio_text + '</i>') if bio_text else ''}"
    )

    try:
        await call.message.delete()
    except Exception:
        pass

    await AvatarCacheService.send_avatar_photo(
        bot=bot,
        chat_id=call.from_user.id,
        avatar_path=new_persona.avatar_path,
        is_custom_photo=False,
        caption=caption,
        reply_markup=get_avatar_choice_keyboard()
    )

@router.callback_query(RegistrationStates.avatar_choice, F.data == "avatar_confirm:rename")
async def process_avatar_rename_prompt(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    is_couple = (data.get("gender") == "couple")
    prompt = "✏️ Введите имя пары или псевдоним:" if is_couple else "✏️ Введи имя или псевдоним для анкеты:"
    await call.message.reply(
        prompt,
        parse_mode="HTML"
    )
    await state.set_state(RegistrationStates.rename)

@router.message(RegistrationStates.rename, F.text)
async def process_custom_rename(message: Message, state: FSMContext, bot: Bot):
    new_name = message.text.strip()
    if len(new_name) < 2 or len(new_name) > 30:
        await message.answer("⚠️ Имя должно быть от 2 до 30 символов. Попробуй еще раз:")
        return

    await state.update_data(first_name=new_name)
    data = await state.get_data()
    is_couple = (data.get("gender") == "couple")
    bio_text = data.get("bio", "")
    avatar_file = data.get("avatar_path")
    couple_age = data.get("couple_age")
    display_age = couple_age if (is_couple and couple_age) else str(data['age'])
    header = "🎭 <b>Ваш тайный образ:</b>\n\n" if is_couple else "🎭 <b>Твой тайный образ:</b>\n\n"
    icon = "👥" if is_couple else "👤"

    caption = (
        f"{header}"
        f"{icon} <b>{new_name}</b>, {display_age}\n"
        f"📍 {data['city']}\n"
        f"{('📝 <i>' + bio_text + '</i>') if bio_text else ''}"
    )

    await state.set_state(RegistrationStates.avatar_choice)
    await AvatarCacheService.send_avatar_photo(
        bot=bot,
        chat_id=message.chat.id,
        avatar_path=avatar_file,
        is_custom_photo=data.get("is_custom_photo", False),
        caption=caption,
        reply_markup=get_avatar_choice_keyboard()
    )

@router.callback_query(RegistrationStates.avatar_choice, F.data == "avatar_confirm:custom")
async def process_avatar_custom_prompt(call: CallbackQuery):
    await call.answer()
    await call.message.reply(
        "📸 Отправь фото сюда в диалог:\n<i>(или нажми «❌ Отмена»)</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )

@router.message(RegistrationStates.avatar_choice, F.photo)
async def process_custom_photo_upload(message: Message, state: FSMContext, bot: Bot):
    photo_id = message.photo[-1].file_id
    await state.update_data(avatar_path=photo_id, is_custom_photo=True)
    await complete_registration(message, state)

@router.callback_query(RegistrationStates.avatar_choice, F.data == "avatar_confirm:keep")
async def process_avatar_keep(call: CallbackQuery, state: FSMContext):
    await call.answer()
    try:
        await call.message.delete_reply_markup()
    except Exception:
        pass
    await complete_registration(call.message, state, user_tg=call.from_user)

async def complete_registration(message: Message, state: FSMContext, user_tg=None):
    from_user = user_tg or message.from_user
    data = await state.get_data()

    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, from_user.id)
        if user:
            await UserService.update_user(
                session=session,
                user_id=user.id,
                username=from_user.username,
                first_name=data["first_name"],
                gender=data["gender"],
                target_gender=data["target_gender"],
                age=data["age"],
                couple_age=data.get("couple_age"),
                city=data["city"],
                bio=data["bio"],
                avatar_path=data["avatar_path"],
                is_custom_photo=data["is_custom_photo"],
                is_active=True
            )
        else:
            ref_tg_id = data.get("referrer_id")
            utm_source = data.get("utm_source")
            new_u = await UserService.create_user(
                session=session,
                telegram_id=from_user.id,
                username=from_user.username,
                first_name=data["first_name"],
                gender=data["gender"],
                target_gender=data["target_gender"],
                age=data["age"],
                couple_age=data.get("couple_age"),
                city=data["city"],
                bio=data["bio"],
                avatar_path=data["avatar_path"],
                is_custom_photo=data["is_custom_photo"],
                referrer_id=ref_tg_id,
                utm_source=utm_source
            )
            # Reward referrer if present
            if ref_tg_id:
                referrer = await UserService.get_by_telegram_id(session, ref_tg_id)
                if referrer:
                    referrer.referral_count = (referrer.referral_count or 0) + 1
                    await session.commit()
                    try:
                        await message.bot.send_message(
                            chat_id=referrer.telegram_id,
                            text="🎉 <b>По вашей ссылке зарегистрировался новый пользователь!</b>\n\n"
                                 "Ваша анкета получила приоритет в топе поиска. Спасибо за приглашение!",
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass

    await state.clear()
    await message.answer(
        "🎉 <b>Анкета готова!</b>\n\n"
        "Жми <b>«🔍 Поиск»</b>, чтобы смотреть анкеты рядом.",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )
