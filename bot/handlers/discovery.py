import os
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.database.db import async_session_maker
from bot.database.models import User
from bot.services.user_service import UserService
from bot.services.matching import MatchingService
from bot.services.chat_service import ChatService
from bot.services.avatar_cache import AvatarCacheService
from bot.keyboards.inline import (
    get_discovery_keyboard,
    get_match_keyboard,
    get_incoming_like_alert_keyboard,
    get_incoming_like_keyboard,
    get_search_filters_keyboard,
    get_filter_age_keyboard,
    get_filter_city_keyboard,
    get_target_gender_keyboard
)
from bot.keyboards.reply import get_main_keyboard, get_cancel_keyboard
from bot.states.profile import SendLikeMessageStates, SearchFilterStates

logger = logging.getLogger(__name__)
router = Router(name="simple_discovery")

async def send_candidate_card(target_chat_id: int, bot: Bot, candidate: User, compliment: str = None):
    caption = UserService.format_caption(candidate, is_owner=False)
    if compliment:
        caption = f"💌 <b>Сообщение:</b> <i>«{compliment}»</i>\n\n" + caption

    keyboard = get_discovery_keyboard(candidate.id)

    try:
        await AvatarCacheService.send_avatar_photo(
            bot=bot,
            chat_id=target_chat_id,
            avatar_path=candidate.avatar_path,
            is_custom_photo=candidate.is_custom_photo,
            caption=caption,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Failed to send profile photo: {e}")
        await bot.send_message(
            chat_id=target_chat_id,
            text=caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

@router.message(F.text.in_({"🔍 Поиск", "🔍 Смотреть анкеты"}))
async def start_discovery(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    async with async_session_maker() as session:
        viewer = await UserService.get_by_telegram_id(session, message.from_user.id)
        if not viewer:
            await message.answer("Сначала создайте анкету через /start.")
            return

        # Сбрасываем активный чат при переходе к поиску
        if viewer.active_chat_id:
            await UserService.set_active_chat(session, viewer.id, None)

        if not viewer.is_active:
            await UserService.set_active(session, viewer.id, True)

        candidate_pair = await MatchingService.get_next_profile(session, viewer)
        if not candidate_pair:
            text = (
                "🏁 <b>Анкеты по вашим фильтрам пока закончились.</b>\n\n"
                f"{format_filters_text(viewer)}"
            )
            kb = get_search_filters_keyboard(
                city=viewer.search_city,
                age_min=viewer.search_age_min or 18,
                age_max=viewer.search_age_max or 99,
                target_gender=viewer.target_gender
            )
            await message.answer(text, reply_markup=kb, parse_mode="HTML")
            return

        candidate, compliment = candidate_pair
        await send_candidate_card(message.from_user.id, bot, candidate, compliment)

@router.callback_query(F.data == "resume_discovery")
async def cb_resume_discovery(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    try:
        await call.message.delete_reply_markup()
    except Exception:
        pass

    async with async_session_maker() as session:
        viewer = await UserService.get_by_telegram_id(session, call.from_user.id)
        if not viewer:
            return

        candidate_pair = await MatchingService.get_next_profile(session, viewer)
        if not candidate_pair:
            text = (
                "🏁 <b>Все доступные анкеты просмотрены.</b>\n\n"
                f"{format_filters_text(viewer)}"
            )
            kb = get_search_filters_keyboard(
                city=viewer.search_city,
                age_min=viewer.search_age_min or 18,
                age_max=viewer.search_age_max or 99,
                target_gender=viewer.target_gender
            )
            await call.message.answer(text, reply_markup=kb, parse_mode="HTML")
            return

        candidate, compliment = candidate_pair
        await send_candidate_card(call.from_user.id, bot, candidate, compliment)

def format_filters_text(viewer: User) -> str:
    city_label = viewer.search_city if viewer.search_city else "Любой 🌍"
    age_min = viewer.search_age_min if viewer.search_age_min is not None else 18
    age_max = viewer.search_age_max if viewer.search_age_max is not None else 99
    age_label = "Любой 🎂" if (age_min <= 18 and age_max >= 90) else f"{age_min}–{age_max} лет 🎂"
    target_map = {"female": "Девушек 👩", "male": "Мужчин 👨", "couple": "Пары 👥", "all": "Всех 🌟"}
    target_label = target_map.get(viewer.target_gender, "Всех 🌟")
    is_couple = (viewer.gender == "couple")
    target_prompt = "🎯 <b>Ищем:</b>" if is_couple else "🎯 <b>Ищу:</b>"
    return (
        "⚙️ <b>Параметры поиска анкет:</b>\n\n"
        f"📍 <b>Город:</b> {city_label}\n"
        f"🎂 <b>Возраст:</b> {age_label}\n"
        f"{target_prompt} {target_label}\n\n"
        "<i>Нажмите на кнопку ниже, чтобы изменить параметр:</i>"
    )

@router.callback_query(F.data == "search_filter:open")
async def cb_open_filters(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    async with async_session_maker() as session:
        viewer = await UserService.get_by_telegram_id(session, call.from_user.id)
        if not viewer:
            return
        text = format_filters_text(viewer)
        kb = get_search_filters_keyboard(
            city=viewer.search_city,
            age_min=viewer.search_age_min or 18,
            age_max=viewer.search_age_max or 99,
            target_gender=viewer.target_gender
        )
        try:
            await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await call.message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "filter_act:city")
async def cb_filter_city_menu(call: CallbackQuery):
    await call.answer()
    async with async_session_maker() as session:
        viewer = await UserService.get_by_telegram_id(session, call.from_user.id)
        if not viewer:
            return
        kb = get_filter_city_keyboard(viewer.city)
        text = "📍 <b>Выберите город поиска:</b>"
        try:
            await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await call.message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("set_f_city:"))
async def cb_set_filter_city(call: CallbackQuery, state: FSMContext):
    await call.answer()
    city_val = call.data.split(":", 1)[1]

    if city_val == "custom":
        await state.set_state(SearchFilterStates.custom_city)
        sent = await call.message.answer(
            "✏️ Напишите название города, в котором хотите искать (например: <i>Москва</i>):",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        await state.update_data(prompt_msg_id=sent.message_id)
        return

    new_city = None if city_val in ("all", "any") else city_val
    async with async_session_maker() as session:
        viewer = await UserService.get_by_telegram_id(session, call.from_user.id)
        if viewer:
            await UserService.update_user(session, viewer.id, search_city=new_city)
            viewer.search_city = new_city
            text = format_filters_text(viewer)
            kb = get_search_filters_keyboard(
                city=viewer.search_city,
                age_min=viewer.search_age_min or 18,
                age_max=viewer.search_age_max or 99,
                target_gender=viewer.target_gender
            )
            try:
                await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
            except Exception:
                await call.message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.message(SearchFilterStates.custom_city)
async def process_custom_filter_city(message: Message, state: FSMContext):
    city_input = message.text.strip().capitalize()
    data = await state.get_data()
    prompt_id = data.get("prompt_msg_id")
    await state.clear()

    try:
        if prompt_id:
            await message.bot.delete_message(message.chat.id, prompt_id)
        await message.delete()
    except Exception:
        pass

    async with async_session_maker() as session:
        viewer = await UserService.get_by_telegram_id(session, message.from_user.id)
        if viewer:
            await UserService.update_user(session, viewer.id, search_city=city_input)
            viewer.search_city = city_input
            text = format_filters_text(viewer)
            kb = get_search_filters_keyboard(
                city=viewer.search_city,
                age_min=viewer.search_age_min or 18,
                age_max=viewer.search_age_max or 99,
                target_gender=viewer.target_gender
            )
            await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "filter_act:age")
async def cb_filter_age_menu(call: CallbackQuery):
    await call.answer()
    kb = get_filter_age_keyboard()
    text = "🎂 <b>Выберите диапазон возраста:</b>"
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("set_f_age:"))
async def cb_set_filter_age(call: CallbackQuery, state: FSMContext):
    await call.answer()
    parts = call.data.split(":")
    if parts[1] == "custom":
        await state.set_state(SearchFilterStates.custom_age)
        sent = await call.message.answer(
            "✏️ Напишите желаемый возраст или диапазон (например: <code>20-30</code> или <code>25</code>):",
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        await state.update_data(prompt_msg_id=sent.message_id)
        return

    age_min = int(parts[1])
    age_max = int(parts[2])

    async with async_session_maker() as session:
        viewer = await UserService.get_by_telegram_id(session, call.from_user.id)
        if viewer:
            await UserService.update_user(session, viewer.id, search_age_min=age_min, search_age_max=age_max)
            viewer.search_age_min = age_min
            viewer.search_age_max = age_max
            text = format_filters_text(viewer)
            kb = get_search_filters_keyboard(
                city=viewer.search_city,
                age_min=viewer.search_age_min or 18,
                age_max=viewer.search_age_max or 99,
                target_gender=viewer.target_gender
            )
            try:
                await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
            except Exception:
                await call.message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.message(SearchFilterStates.custom_age)
async def process_custom_filter_age(message: Message, state: FSMContext):
    raw = message.text.strip().replace(" ", "")
    data = await state.get_data()
    prompt_id = data.get("prompt_msg_id")
    await state.clear()

    try:
        if prompt_id:
            await message.bot.delete_message(message.chat.id, prompt_id)
        await message.delete()
    except Exception:
        pass

    age_min, age_max = 18, 99
    try:
        if "-" in raw:
            p = raw.split("-")
            age_min = max(18, int(p[0]))
            age_max = min(99, int(p[1]))
        else:
            single = int(raw)
            age_min = max(18, single - 3)
            age_max = min(99, single + 3)
    except Exception:
        age_min, age_max = 18, 99

    async with async_session_maker() as session:
        viewer = await UserService.get_by_telegram_id(session, message.from_user.id)
        if viewer:
            await UserService.update_user(session, viewer.id, search_age_min=age_min, search_age_max=age_max)
            viewer.search_age_min = age_min
            viewer.search_age_max = age_max
            text = format_filters_text(viewer)
            kb = get_search_filters_keyboard(
                city=viewer.search_city,
                age_min=viewer.search_age_min or 18,
                age_max=viewer.search_age_max or 99,
                target_gender=viewer.target_gender
            )
            await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "filter_act:target")
async def cb_filter_target_menu(call: CallbackQuery):
    await call.answer()
    kb = get_target_gender_keyboard(prefix="set_f_target")
    text = "🎯 <b>Кого вы хотите искать?</b>"
    try:
        await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("set_f_target:"))
async def cb_set_filter_target(call: CallbackQuery):
    await call.answer()
    new_target = call.data.split(":")[1]
    async with async_session_maker() as session:
        viewer = await UserService.get_by_telegram_id(session, call.from_user.id)
        if viewer:
            await UserService.update_user(session, viewer.id, target_gender=new_target)
            viewer.target_gender = new_target
            text = format_filters_text(viewer)
            kb = get_search_filters_keyboard(
                city=viewer.search_city,
                age_min=viewer.search_age_min or 18,
                age_max=viewer.search_age_max or 99,
                target_gender=viewer.target_gender
            )
            try:
                await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
            except Exception:
                await call.message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "filter_act:start")
async def cb_filter_start(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    try:
        await call.message.delete()
    except Exception:
        pass

    async with async_session_maker() as session:
        viewer = await UserService.get_by_telegram_id(session, call.from_user.id)
        if not viewer:
            return

        candidate_pair = await MatchingService.get_next_profile(session, viewer)
        if not candidate_pair:
            text = (
                "🏁 <b>Анкеты по вашим фильтрам пока закончились.</b>\n\n"
                f"{format_filters_text(viewer)}"
            )
            kb = get_search_filters_keyboard(
                city=viewer.search_city,
                age_min=viewer.search_age_min or 18,
                age_max=viewer.search_age_max or 99,
                target_gender=viewer.target_gender
            )
            await call.message.answer(text, reply_markup=kb, parse_mode="HTML")
            return

        candidate, compliment = candidate_pair
        await send_candidate_card(call.from_user.id, bot, candidate, compliment)


@router.callback_query(F.data.startswith("like:"))
async def process_like(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    target_user_id = int(call.data.split(":")[1])
    try:
        await call.message.delete_reply_markup()
    except Exception:
        pass

    async with async_session_maker() as session:
        viewer = await UserService.get_by_telegram_id(session, call.from_user.id)
        if not viewer:
            return

        is_match, target_user = await MatchingService.record_reaction(
            session=session,
            from_user=viewer,
            target_user_id=target_user_id,
            reaction_type="like",
            bot=bot
        )

        if is_match and target_user:
            chat_session = await ChatService.create_or_get_session(session, viewer.id, target_user.id)

            await call.message.answer(
                f"🎉 <b>Взаимная симпатия с {target_user.first_name}!</b>\n\n"
                "Начните анонимный диалог прямо сейчас:",
                reply_markup=get_match_keyboard(chat_session.id),
                parse_mode="HTML"
            )

            try:
                await bot.send_message(
                    chat_id=target_user.telegram_id,
                    text=(
                        f"🎉 <b>Взаимная симпатия с {viewer.first_name}!</b>\n\n"
                        "Начните анонимный диалог прямо сейчас:"
                    ),
                    reply_markup=get_match_keyboard(chat_session.id),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to notify match: {e}")

            return
        else:
            if target_user:
                try:
                    await bot.send_message(
                        chat_id=target_user.telegram_id,
                        text="💖 <b>Кому-то понравилась ваша анкета!</b>",
                        reply_markup=get_incoming_like_alert_keyboard(),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.debug(f"Failed to send like notification: {e}")

        # Показываем следующего
        candidate_pair = await MatchingService.get_next_profile(session, viewer)
        if candidate_pair:
            candidate, compliment = candidate_pair
            await send_candidate_card(call.from_user.id, bot, candidate, compliment)
        else:
            await call.message.answer(
                "🏁 Все анкеты просмотрены. Загляните позже!",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )

@router.callback_query(F.data.startswith("dislike:"))
async def process_dislike(call: CallbackQuery, state: FSMContext, bot: Bot):
    await call.answer()
    target_user_id = int(call.data.split(":")[1])
    try:
        await call.message.delete_reply_markup()
    except Exception:
        pass

    async with async_session_maker() as session:
        viewer = await UserService.get_by_telegram_id(session, call.from_user.id)
        if viewer:
            await MatchingService.record_reaction(
                session=session,
                from_user=viewer,
                target_user_id=target_user_id,
                reaction_type="dislike"
            )

            candidate_pair = await MatchingService.get_next_profile(session, viewer)
            if candidate_pair:
                candidate, compliment = candidate_pair
                await send_candidate_card(call.from_user.id, bot, candidate, compliment)
            else:
                await call.message.answer(
                    "🏁 Все анкеты просмотрены. Загляните позже!",
                    reply_markup=get_main_keyboard(),
                    parse_mode="HTML"
                )

@router.callback_query(F.data.startswith("msg:"))
async def process_msg_prompt(call: CallbackQuery, state: FSMContext):
    await call.answer()
    target_user_id = int(call.data.split(":")[1])
    await state.set_state(SendLikeMessageStates.message)
    await state.update_data(target_user_id=target_user_id)
    await call.message.reply(
        "💌 Напишите короткое сообщение к лайку:\n<i>(или нажмите «❌ Отмена»)</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )

@router.message(SendLikeMessageStates.message, F.text)
async def process_msg_send(message: Message, state: FSMContext, bot: Bot):
    compliment = message.text.strip()
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    await state.clear()

    async with async_session_maker() as session:
        viewer = await UserService.get_by_telegram_id(session, message.from_user.id)
        if not viewer or not target_user_id:
            await message.answer("Произошла ошибка, попробуйте снова.", reply_markup=get_main_keyboard())
            return

        is_match, target_user = await MatchingService.record_reaction(
            session=session,
            from_user=viewer,
            target_user_id=target_user_id,
            reaction_type="like",
            message=compliment,
            bot=bot
        )

        await message.answer("💌 Сообщение и лайк отправлены!", reply_markup=get_main_keyboard())

        if is_match and target_user:
            chat_session = await ChatService.create_or_get_session(session, viewer.id, target_user.id)
            await message.answer(
                f"🎉 <b>Взаимная симпатия с {target_user.first_name}!</b>\n\n"
                "Начните анонимный диалог прямо сейчас:",
                reply_markup=get_match_keyboard(chat_session.id),
                parse_mode="HTML"
            )
            try:
                await bot.send_message(
                    chat_id=target_user.telegram_id,
                    text=(
                        f"🎉 <b>Взаимная симпатия с {viewer.first_name}!</b>\n\n"
                        "Начните анонимный диалог прямо сейчас:"
                    ),
                    reply_markup=get_match_keyboard(chat_session.id),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to notify match: {e}")
            return
        else:
            if target_user:
                try:
                    await bot.send_message(
                        chat_id=target_user.telegram_id,
                        text="💌 <b>Вам оставили сообщение и лайк!</b>",
                        reply_markup=get_incoming_like_alert_keyboard(),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.debug(f"Failed to send like notification: {e}")

        candidate_pair = await MatchingService.get_next_profile(session, viewer)
        if candidate_pair:
            candidate, comp = candidate_pair
            await send_candidate_card(message.from_user.id, bot, candidate, comp)
        else:
            await message.answer("🏁 Все анкеты просмотрены. Загляните позже!", reply_markup=get_main_keyboard())

@router.callback_query(F.data == "show_likes_list")
async def cb_show_likes_list(call: CallbackQuery, bot: Bot):
    await call.answer()
    try:
        await call.message.delete_reply_markup()
    except Exception:
        pass

    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        if not user:
            return

        incoming = await MatchingService.get_incoming_likes(session, user.id)
        if not incoming:
            await call.message.answer(
                "💌 <b>Новых симпатий пока нет.</b>\nПродолжайте поиск в «🔍 Поиск»!",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            return

        await call.message.answer(f"💌 <b>Вам поставили лайк ({len(incoming)}):</b>", parse_mode="HTML")
        for sender, compliment in incoming[:3]:
            cap = UserService.format_caption(sender, is_owner=False)
            if compliment:
                cap = f"💌 <b>Сообщение:</b> <i>«{compliment}»</i>\n\n" + cap
            await AvatarCacheService.send_avatar_photo(
                bot=bot,
                chat_id=call.from_user.id,
                avatar_path=sender.avatar_path,
                is_custom_photo=sender.is_custom_photo,
                caption=cap,
                reply_markup=get_incoming_like_keyboard(sender.id)
            )

@router.callback_query(F.data.startswith("report:"))
async def process_report(call: CallbackQuery, bot: Bot):
    await call.answer()
    target_user_id = int(call.data.split(":")[1])
    try:
        await call.message.delete_reply_markup()
    except Exception:
        pass

    async with async_session_maker() as session:
        viewer = await UserService.get_by_telegram_id(session, call.from_user.id)
        if viewer:
            await UserService.report_user(session, viewer.id, target_user_id, "Жалоба на анкету")
            await MatchingService.record_reaction(session, viewer, target_user_id, "dislike")
            await call.message.answer("🛡️ Жалоба принята. Пользователь скрыт.")

            candidate_pair = await MatchingService.get_next_profile(session, viewer)
            if candidate_pair:
                candidate, comp = candidate_pair
                await send_candidate_card(call.from_user.id, bot, candidate, comp)
            else:
                await call.message.answer("🏁 Все анкеты просмотрены!", reply_markup=get_main_keyboard())
