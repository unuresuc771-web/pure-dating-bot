from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from bot.keyboards.reply import get_main_keyboard
from bot.database.db import async_session_maker
from bot.services.user_service import UserService

router = Router(name="simple_common")

@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "✨ <b>Бот простых и удобных знакомств</b> ✨\n\n"
        "<b>Как пользоваться ботом:</b>\n"
        "1. 🔍 <b>«Смотреть анкеты»</b> — листайте анкеты людей рядом. Ставьте ❤️, если понравились, или 👎, чтобы листать дальше.\n"
        "2. 💌 <b>«С сообщением»</b> — отправляйте комплимент или приятные слова сразу с лайком.\n"
        "3. 🎉 <b>Взаимная симпатия</b> — если вам ответили взаимностью, бот сразу пришлёт прямую ссылку на профиль Telegram для общения!\n"
        "4. 💌 <b>«Кому я нравлюсь»</b> — список тех, кто поставил вам лайк.\n"
        "5. 👤 <b>«Моя анкета»</b> — просмотр и быстрое изменение своих данных или аватара.\n\n"
        "<b>Команды:</b>\n"
        "• <b>/start</b> — Главное меню\n"
        "• <b>/help</b> — Справка\n"
        "• <b>❌ Отмена</b> — Сброс текущего действия в любой момент"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "❌ Отмена")
async def action_cancel(message: Message, state: FSMContext):
    await state.clear()
    async with async_session_maker() as session:
        user = await UserService.get_by_telegram_id(session, message.from_user.id)
        if user:
            await message.answer("👌 Действие отменено.", reply_markup=get_main_keyboard())
        else:
            await message.answer("👌 Действие отменено. Напишите /start для начала.")
