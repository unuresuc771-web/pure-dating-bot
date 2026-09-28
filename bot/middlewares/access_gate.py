import logging
from typing import Any, Awaitable, Callable, Dict, Set
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from bot.database.db import async_session_maker
from bot.database.models import User
from bot.services.admin_service import AdminService
from bot.services.user_service import UserService
from bot.config import settings

logger = logging.getLogger(__name__)

class AccessGateMiddleware(BaseMiddleware):
    cached_authorized_ids: Set[int] = set()
    unlocked_personal_ids: Set[int] = set()

    def __init__(self):
        super().__init__()

    @classmethod
    def unlock_user(cls, tg_id: int):
        cls.unlocked_personal_ids.add(tg_id)

    @classmethod
    def lock_user(cls, tg_id: int):
        cls.unlocked_personal_ids.discard(tg_id)

    @classmethod
    def is_user_unlocked(cls, tg_id: int) -> bool:
        return tg_id in cls.unlocked_personal_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_tg = None
        if isinstance(event, Message) and event.from_user:
            user_tg = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            user_tg = event.from_user

        if not user_tg:
            return await handler(event, data)

        tg_id = user_tg.id

        # 1. Admin bypass
        if AdminService.is_admin_id(tg_id):
            # Still record activity for admin if registered
            try:
                async with async_session_maker() as session:
                    user = await UserService.get_by_telegram_id(session, tg_id)
                    if user and not user.is_fake:
                        await AdminService.record_user_activity(session, user.id)
            except Exception as e:
                logger.error(f"Error recording admin activity: {e}")
            return await handler(event, data)

        # 2. Gate check (Global password vs Personal password)
        try:
            async with async_session_maker() as session:
                pass_enabled = await AdminService.is_password_protection_enabled(session)
                
                # Fetch user
                user = await UserService.get_by_telegram_id(session, tg_id)
                if user and not user.is_fake:
                    try:
                        await AdminService.record_user_activity(session, user.id)
                    except Exception as e:
                        logger.error(f"Error recording user activity: {e}")

                # CASE A: Global closed-beta gate is enabled by Admin
                if pass_enabled:
                    if tg_id in self.cached_authorized_ids:
                        return await handler(event, data)

                    is_auth = await AdminService.is_user_authorized_for_gate(session, tg_id)
                    if is_auth:
                        self.cached_authorized_ids.add(tg_id)
                        return await handler(event, data)

                    # Check if user is submitting global password
                    if isinstance(event, Message) and event.text:
                        text_input = event.text.strip()
                        if text_input.startswith("/admin"):
                            return await handler(event, data)

                        access_pass = await AdminService.get_access_password(session)
                        admin_pass = await AdminService.get_setting(session, "admin_password", AdminService.DEFAULT_ADMIN_PASSWORD)
                        
                        is_valid = False
                        if access_pass and text_input.lower() == access_pass.lower():
                            is_valid = True
                        elif admin_pass and text_input.lower() == admin_pass.lower():
                            is_valid = True

                        if is_valid:
                            await AdminService.authorize_user_for_gate(session, tg_id)
                            self.cached_authorized_ids.add(tg_id)
                            await event.answer(
                                "🔓 <b>Пароль принят! Добро пожаловать.</b>\n\n"
                                "Нажмите /start, чтобы начать знакомства.",
                                parse_mode="HTML"
                            )
                            return None
                        else:
                            await event.answer(
                                "🔒 <b>Вход по паролю</b>\n\n"
                                "Бот работает в приватном режиме.\n"
                                "Пожалуйста, введите пароль для доступа к сервису:",
                                parse_mode="HTML"
                            )
                            return None
                    elif isinstance(event, CallbackQuery):
                        await event.answer("🔒 Вход по паролю. Введите пароль в чат бота.", show_alert=True)
                        return None

                # CASE B: Global gate is OFF (standard mode), check user's PERSONAL password
                if user and user.personal_password:
                    if tg_id not in self.unlocked_personal_ids:
                        # User is currently locked with personal PIN
                        if isinstance(event, Message) and event.text:
                            text_input = event.text.strip()
                            if text_input.lower() == user.personal_password.strip().lower():
                                self.unlock_user(tg_id)
                                from bot.keyboards.reply import get_main_keyboard
                                await event.answer(
                                    f"🔓 <b>Личный пароль принят! Добро пожаловать, {user.first_name}.</b>",
                                    reply_markup=get_main_keyboard(has_lock=True),
                                    parse_mode="HTML"
                                )
                                return None
                            else:
                                await event.answer(
                                    "🔒 <b>Вход защищен вашим личным паролем</b>\n\n"
                                    "Пожалуйста, введите ваш персональный PIN/пароль для продолжения:",
                                    parse_mode="HTML"
                                )
                                return None
                        elif isinstance(event, CallbackQuery):
                            await event.answer("🔒 Введите ваш личный пароль в чат для разблокировки.", show_alert=True)
                            return None

        except Exception as e:
            logger.error(f"Error in AccessGateMiddleware: {e}", exc_info=True)
            return await handler(event, data)

        return await handler(event, data)
