from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.database.db import async_session_maker
from bot.services.user_service import UserService
from bot.services.devils_bones_service import DevilsBonesService
from bot.services.chat_service import ChatService
from bot.keyboards.reply import get_pure_main_menu, get_in_chat_reply_keyboard
from bot.keyboards.inline import get_in_chat_action_bar

router = Router(name="pure_devils_bones")

@router.message(F.text == "🎲 Кости дьявола")
async def process_devils_bones(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Сначала пройдите регистрацию через /start.")
            return

        chat_session, partner = await DevilsBonesService.roll_the_bones(session, user)

        if chat_session and partner:
            # Моментальное соединение!
            await UserService.set_active_chat(session, user.id, chat_session.id)
            await UserService.set_active_chat(session, partner.id, chat_session.id)

            my_nick, partner_nick, _ = ChatService.get_user_display_name_and_partner_id(chat_session, user.id)
            partner_my_nick, partner_partner_nick, _ = ChatService.get_user_display_name_and_partner_id(chat_session, partner.id)
            time_str = ChatService.get_remaining_time_str(chat_session)

            await message.answer(
                f"🎲 <b>КОСТИ ДЬЯВОЛА СЫГРАЛИ!</b> 🎲\n\n"
                f"Вы моментально соединены со случайным анонимным собеседником онлайн!\n\n"
                f"🎭 <b>Ваш псевдоним:</b> {my_nick}\n"
                f"👤 <b>Собеседник:</b> {partner_nick}\n\n"
                f"<i>Чат активен 24 часа. Начните общение прямо сейчас!</i>",
                reply_markup=get_in_chat_reply_keyboard(),
                parse_mode="HTML"
            )
            await message.answer(
                f"⏳ <b>Панель управления #{chat_session.id}</b>",
                reply_markup=get_in_chat_action_bar(chat_session.id, time_str)
            )

            try:
                await bot.send_message(
                    partner.telegram_id,
                    f"🎲 <b>КОСТИ ДЬЯВОЛА СЫГРАЛИ!</b> 🎲\n\n"
                    f"Спонтанное анонимное соединение онлайн!\n\n"
                    f"🎭 <b>Ваш псевдоним:</b> {partner_my_nick}\n"
                    f"👤 <b>Собеседник:</b> {partner_partner_nick}\n\n"
                    f"<i>Напишите первое сообщение!</i>",
                    reply_markup=get_in_chat_reply_keyboard(),
                    parse_mode="HTML"
                )
                await bot.send_message(
                    partner.telegram_id,
                    f"⏳ <b>Панель управления #{chat_session.id}</b>",
                    reply_markup=get_in_chat_action_bar(chat_session.id, time_str)
                )
            except Exception:
                pass
        else:
            await message.answer(
                "🎲 <b>Кости дьявола брошены!</b>\n\n"
                "Вы добавлены в очередь спонтанных знакомств. Как только другой свободный пользователь нажмет кнопку — бот моментально откроет между вами анонимный диалог.\n\n"
                "<i>Пока вы ждете, можете полистать «🔥 Лента Pure»!</i>",
                reply_markup=get_pure_main_menu(),
                parse_mode="HTML"
            )
