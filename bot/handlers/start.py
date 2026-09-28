import html
from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.database.db import async_session_maker
from bot.services.user_service import UserService
from bot.keyboards.reply import get_main_keyboard
from bot.handlers.registration import start_simple_registration

router = Router(name="simple_start")

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, command: CommandObject):
    ref_payload = command.args
    referrer_id = None
    utm_source = None

    if ref_payload:
        clean_payload = ref_payload.strip()
        if clean_payload.startswith("ref_"):
            try:
                candidate_id = int(clean_payload.replace("ref_", ""))
                if candidate_id != message.from_user.id:
                    referrer_id = candidate_id
            except ValueError:
                pass
        elif clean_payload.startswith("utm_"):
            utm_source = clean_payload.replace("utm_", "")[:64]
        else:
            utm_source = clean_payload[:64]

    await state.clear()
    if referrer_id or utm_source:
        await state.update_data(referrer_id=referrer_id, utm_source=utm_source)

    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if not user:
            await start_simple_registration(message, state)
            return

        if user.active_chat_id:
            await UserService.set_active_chat(session, user.id, None)

        if message.from_user.username != user.username:
            await UserService.update_user(session, user.id, username=message.from_user.username)

        has_lock = bool(user.personal_password)
        safe_name = html.escape(user.first_name or "Пользователь")
        await message.answer(
            f"👋 С возвращением, <b>{safe_name}</b>!\n\n"
            "Выберите раздел в меню:",
            reply_markup=get_main_keyboard(has_lock=has_lock),
            parse_mode="HTML"
        )
