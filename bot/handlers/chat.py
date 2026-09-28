import logging
import asyncio
from typing import Optional
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.database.db import async_session_maker
from bot.database.models import User, SecretMedia, utc_now
from bot.services.user_service import UserService
from bot.services.chat_service import ChatService
from bot.states.chat import ChatStates
from bot.keyboards.reply import get_main_keyboard, get_in_chat_reply_keyboard
from bot.keyboards.inline import (
    get_user_chats_keyboard,
    get_confirm_burn_keyboard,
    get_new_message_alert_keyboard,
    get_secret_timer_keyboard,
    get_view_secret_keyboard
)

logger = logging.getLogger(__name__)
router = Router(name="pure_chat")

async def auto_delete_secret(
    bot: Bot,
    recipient_chat_id: int,
    photo_msg_id: int,
    sender_chat_id: int,
    sender_msg_id: Optional[int],
    delay: int
):
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=recipient_chat_id, message_id=photo_msg_id)
    except Exception:
        pass
    if sender_msg_id:
        try:
            await bot.delete_message(chat_id=sender_chat_id, message_id=sender_msg_id)
        except Exception:
            pass

@router.message(F.text.in_({"💬 Чаты", "💬 Мои чаты", "◀️ Все чаты"}))
async def show_user_chats(message: Message, state: FSMContext):
    await state.clear()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if not user:
            return

        await UserService.set_active_chat(session, user.id, None)

        chats = await ChatService.get_user_active_sessions(session, user.id)
        if not chats:
            await message.answer(
                "💬 <b>У вас пока нет активных диалогов.</b>\n\n"
                "Ставьте взаимные лайки в поиске, чтобы начать общение!",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            return

        await message.answer(
            f"💬 <b>Активные диалоги ({len(chats)}):</b>\nВыберите собеседника:",
            reply_markup=get_user_chats_keyboard(chats),
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("open_chat:"))
async def cb_open_chat(call: CallbackQuery, state: FSMContext):
    await call.answer()
    session_id = int(call.data.split(":")[1])

    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        chat = await ChatService.get_session_by_id(session, session_id)
        if not user or not chat or chat.status != "active":
            await call.message.answer("Этот диалог уже завершен.", reply_markup=get_main_keyboard())
            return

        if user.id not in (chat.user_a_id, chat.user_b_id):
            return

        partner_id = ChatService.get_partner_id(chat, user.id)
        partner = await UserService.get_by_id(session, partner_id)
        if not partner:
            return

        await UserService.set_active_chat(session, user.id, chat.id)
        await state.set_state(ChatStates.in_chat)
        await state.update_data(session_id=chat.id, partner_id=partner.id)

        try:
            await call.message.delete_reply_markup()
        except Exception:
            pass

        # Полный zero digital footprint: никаких цитирований истории и напоминаний
        await call.message.answer(
            f"💬 <b>Чат с {partner.first_name}</b>",
            reply_markup=get_in_chat_reply_keyboard(),
            parse_mode="HTML"
        )

        # Если собеседник виртуальный и сообщений еще нет - отправляем приветствие
        if partner.is_fake:
            recent_msgs = await ChatService.get_recent_messages(session, chat.id, limit=1)
            if not recent_msgs:
                from bot.services.virtual_chat_engine import VirtualChatEngine
                asyncio.create_task(
                    VirtualChatEngine.process_virtual_reply(
                        bot=call.bot,
                        session_id=chat.id,
                        real_user=user,
                        fake_user=partner,
                        user_message_text="[Начало диалога]"
                    )
                )

@router.message(F.text.in_({"🚪 В меню", "🚪 Выйти в меню (свернуть)", "🚪 Выйти в меню", "🚪 Выйти"}))
async def action_exit_chat(message: Message, state: FSMContext):
    await state.clear()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if user:
            await UserService.set_active_chat(session, user.id, None)

    await message.answer(
        "🚪 Чат свёрнут.",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text.in_({"🔥 Завершить чат", "🔥 Завершить и удалить чат"}))
async def msg_burn_prompt(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")

    if not session_id:
        async with async_session_maker() as session:
            user = await UserService.get_by_telegram_id(session, message.from_user.id)
            if user and user.active_chat_id:
                session_id = user.active_chat_id

    if not session_id:
        await message.answer("У вас нет активного открытого диалога.", reply_markup=get_main_keyboard())
        return

    await message.answer(
        "⚠️ <b>Удалить чат?</b>\nВся переписка и файлы исчезнут навсегда у обоих участников.",
        reply_markup=get_confirm_burn_keyboard(session_id),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("cancel_burn:"))
async def cb_cancel_burn(call: CallbackQuery):
    await call.answer("Отменено")
    try:
        await call.message.delete()
    except Exception:
        pass

@router.callback_query(F.data.startswith("confirm_burn:"))
async def cb_confirm_burn(call: CallbackQuery, bot: Bot, state: FSMContext):
    await call.answer()
    session_id = int(call.data.split(":")[1])
    try:
        await call.message.delete()
    except Exception:
        pass

    await state.clear()

    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, call.from_user.id)
        if not user:
            return

        success, user_a, user_b = await ChatService.burn_and_close_chat(
            bot=bot,
            session=session,
            session_id=session_id,
            closed_by_user_id=user.id
        )

        if not success:
            await call.message.answer("Диалог уже был завершён.", reply_markup=get_main_keyboard())
            return

        partner = user_b if user.id == user_a.id else user_a
        await call.message.answer(
            "💥 <b>Чат удалён без следа.</b>",
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )

        if partner:
            try:
                await bot.send_message(
                    partner.telegram_id,
                    "💥 <b>Собеседник завершил чат.</b> Переписка и файлы стёрты.",
                    reply_markup=get_main_keyboard(),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.debug(f"Failed to notify partner of burned chat: {e}")

# --- Секретные самоуничтожающиеся фото ---

@router.callback_query(F.data.startswith("set_sec_timer:"))
async def cb_set_secret_timer(call: CallbackQuery, bot: Bot):
    await call.answer()
    _, secret_id_str, duration_str = call.data.split(":")
    secret_id = int(secret_id_str)
    duration = int(duration_str)

    async with async_session_maker() as session:
        secret = await session.get(SecretMedia, secret_id)
        if not secret or secret.is_viewed:
            await call.message.edit_text("Фото уже не доступно.")
            return

        sender = await UserService.get_by_id(session, secret.sender_id)
        partner = await UserService.get_by_id(session, secret.recipient_id)
        chat = await ChatService.get_session_by_id(session, secret.session_id)
        if not sender or not partner or not chat or chat.status != "active":
            await call.message.edit_text("Чат больше не активен.")
            return

        partner_in_chat = (partner.active_chat_id == chat.id)
        reply_markup = None if partner_in_chat else get_new_message_alert_keyboard(chat.id)

        if duration == 0:
            # Обычное фото
            cap = f"<b>{sender.first_name}:</b> {secret.caption}" if secret.caption else f"📸 <b>{sender.first_name}</b>"
            sent_msg = await bot.send_photo(
                chat_id=partner.telegram_id,
                photo=secret.file_id,
                caption=cap,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            await call.message.edit_text("📷 Фото отправлено.")
            if sent_msg:
                await ChatService.record_relayed_message(
                    session=session,
                    session_id=chat.id,
                    sender_id=sender.id,
                    sender_message_id=secret.sender_msg_id or call.message.message_id,
                    recipient_message_id=sent_msg.message_id,
                    text=secret.caption or "[Фото]",
                    media_type="photo"
                )
        else:
            # Секретное фото с таймером
            secret.duration = duration
            await session.commit()

            await call.message.edit_text(
                f"🔥 Секретное фото отправлено (самоуничтожится через {duration} сек после открытия)."
            )

            teaser_msg = await bot.send_message(
                chat_id=partner.telegram_id,
                text=(
                    f"🔥 <b>Секретное фото от {sender.first_name}</b>\n\n"
                    f"Одноразовый просмотр: <b>{duration} сек</b>."
                ),
                reply_markup=get_view_secret_keyboard(secret.id, duration),
                parse_mode="HTML"
            )

            if teaser_msg:
                await ChatService.record_relayed_message(
                    session=session,
                    session_id=chat.id,
                    sender_id=sender.id,
                    sender_message_id=secret.sender_msg_id or call.message.message_id,
                    recipient_message_id=teaser_msg.message_id,
                    text="[Скрытое фото]",
                    media_type="secret_photo"
                )

@router.callback_query(F.data.startswith("view_secret:"))
async def cb_view_secret(call: CallbackQuery, bot: Bot):
    await call.answer()
    secret_id = int(call.data.split(":")[1])

    async with async_session_maker() as session:
        secret = await session.get(SecretMedia, secret_id)
        if not secret:
            await call.answer("Фото не найдено.", show_alert=True)
            return

        if secret.is_viewed:
            await call.answer("Это фото уже было открыто и удалено навсегда!", show_alert=True)
            try:
                await call.message.delete()
            except Exception:
                pass
            return

        sender = await UserService.get_by_id(session, secret.sender_id)
        chat = await ChatService.get_session_by_id(session, secret.session_id)
        sender_name = sender.first_name if sender else "Собеседник"

        secret.is_viewed = True
        secret.viewed_at = utc_now()
        await session.commit()

        # Удаляем тизер-сообщение
        try:
            await call.message.delete()
        except Exception:
            pass

        cap = f"🔥 <b>{sender_name}</b>"
        if secret.caption:
            cap += f": {secret.caption}"
        cap += f"\n<i>⏱ Самоуничтожится через {secret.duration} сек...</i>"

        # Отправляем фото со спойлером Telegram
        sent_photo = await bot.send_photo(
            chat_id=call.from_user.id,
            photo=secret.file_id,
            caption=cap,
            has_spoiler=True,
            parse_mode="HTML"
        )

        if chat and sent_photo:
            await ChatService.record_relayed_message(
                session=session,
                session_id=chat.id,
                sender_id=secret.sender_id,
                sender_message_id=secret.sender_msg_id or sent_photo.message_id,
                recipient_message_id=sent_photo.message_id,
                text="[Просмотренное скрытое фото]",
                media_type="secret_photo"
            )

        # Запускаем фоновую задачу самоуничтожения
        sender_tg_id = sender.telegram_id if sender else call.from_user.id
        asyncio.create_task(
            auto_delete_secret(
                bot=bot,
                recipient_chat_id=call.from_user.id,
                photo_msg_id=sent_photo.message_id,
                sender_chat_id=sender_tg_id,
                sender_msg_id=secret.sender_msg_id,
                delay=secret.duration
            )
        )

# --- Маршрутизация сообщений и файлов внутри чата ---

@router.message(ChatStates.in_chat, ~F.text.startswith("/"))
async def handle_in_chat_relay(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")
    partner_id = data.get("partner_id")

    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if not user or not session_id:
            await state.clear()
            return

        chat = await ChatService.get_session_by_id(session, session_id)
        if not chat or chat.status != "active":
            await state.clear()
            await UserService.set_active_chat(session, user.id, None)
            await message.answer("Диалог уже завершён.", reply_markup=get_main_keyboard())
            return

        if not partner_id:
            partner_id = ChatService.get_partner_id(chat, user.id)

        partner = await UserService.get_by_id(session, partner_id)
        if not partner:
            return

        # Специальная обработка для виртуальных собеседников (симуляция живого диалога)
        if partner.is_fake:
            msg_text = message.text or (message.caption if (message.photo or message.video) else "[Медиа]")
            media_type = "photo" if message.photo else ("voice" if message.voice else ("video" if message.video else "text"))

            if message.photo:
                await message.reply("🔥 <i>Собеседник просматривает ваше фото...</i>", parse_mode="HTML")

            await ChatService.record_relayed_message(
                session=session,
                session_id=chat.id,
                sender_id=user.id,
                sender_message_id=message.message_id,
                recipient_message_id=message.message_id,
                text=msg_text,
                media_type=media_type
            )

            from bot.services.virtual_chat_engine import VirtualChatEngine
            asyncio.create_task(
                VirtualChatEngine.process_virtual_reply(
                    bot=bot,
                    session_id=chat.id,
                    real_user=user,
                    fake_user=partner,
                    user_message_text=msg_text or ""
                )
            )
            return

        partner_in_chat = (partner.active_chat_id == chat.id)
        reply_markup = None if partner_in_chat else get_new_message_alert_keyboard(chat.id)

        # Если отправлена фотография — предлагаем таймер скрытого фото
        if message.photo:
            photo_id = message.photo[-1].file_id
            secret = SecretMedia(
                session_id=chat.id,
                sender_id=user.id,
                recipient_id=partner.id,
                file_id=photo_id,
                caption=message.caption,
                sender_msg_id=message.message_id,
                duration=30,
                is_viewed=False
            )
            session.add(secret)
            await session.commit()
            await session.refresh(secret)

            await message.reply(
                "🔥 <b>Скрытое фото</b>\nВыберите время до самоуничтожения:",
                reply_markup=get_secret_timer_keyboard(secret.id),
                parse_mode="HTML"
            )
            return

        try:
            sent_msg = None
            msg_text = None
            media_type = "text"

            if message.text:
                msg_text = message.text
                media_type = "text"
                sent_msg = await bot.send_message(
                    chat_id=partner.telegram_id,
                    text=f"<b>{user.first_name}:</b> {message.text}",
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            elif message.voice:
                media_type = "voice"
                msg_text = "[Голосовое]"
                sent_msg = await bot.send_voice(
                    chat_id=partner.telegram_id,
                    voice=message.voice.file_id,
                    caption=f"🎤 <b>{user.first_name}</b>",
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            elif message.video_note:
                media_type = "video_note"
                msg_text = "[Кружочек]"
                sent_msg = await bot.send_video_note(
                    chat_id=partner.telegram_id,
                    video_note=message.video_note.file_id,
                    reply_markup=reply_markup
                )
            elif message.video:
                media_type = "video"
                msg_text = message.caption or "[Видео]"
                cap = f"📹 <b>{user.first_name}:</b> {message.caption}" if message.caption else f"📹 <b>{user.first_name}</b>"
                sent_msg = await bot.send_video(
                    chat_id=partner.telegram_id,
                    video=message.video.file_id,
                    caption=cap,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            elif message.sticker:
                media_type = "sticker"
                msg_text = "[Стикер]"
                sent_msg = await bot.send_sticker(
                    chat_id=partner.telegram_id,
                    sticker=message.sticker.file_id,
                    reply_markup=reply_markup
                )

            if sent_msg:
                await ChatService.record_relayed_message(
                    session=session,
                    session_id=chat.id,
                    sender_id=user.id,
                    sender_message_id=message.message_id,
                    recipient_message_id=sent_msg.message_id,
                    text=msg_text,
                    media_type=media_type
                )
        except Exception as e:
            logger.error(f"Failed to relay message in chat {chat.id}: {e}")
