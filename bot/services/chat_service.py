import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from aiogram import Bot
from sqlalchemy import select, or_, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, ChatSession, ChatMessage, utc_now

logger = logging.getLogger(__name__)

class ChatService:
    @staticmethod
    async def create_or_get_session(
        session: AsyncSession,
        user_a_id: int,
        user_b_id: int
    ) -> ChatSession:
        u1, u2 = min(user_a_id, user_b_id), max(user_a_id, user_b_id)

        # Проверяем, есть ли уже активная сессия
        stmt = select(ChatSession).where(
            ChatSession.user_a_id == u1,
            ChatSession.user_b_id == u2,
            ChatSession.status == "active"
        )
        res = await session.execute(stmt)
        chat = res.scalar_one_or_none()
        if chat:
            return chat

        new_chat = ChatSession(
            user_a_id=u1,
            user_b_id=u2,
            status="active",
            created_at=utc_now()
        )
        session.add(new_chat)
        await session.commit()
        await session.refresh(new_chat)
        return new_chat

    @staticmethod
    async def get_session_by_id(session: AsyncSession, session_id: int) -> Optional[ChatSession]:
        return await session.get(ChatSession, session_id)

    @staticmethod
    async def get_user_active_sessions(session: AsyncSession, user_id: int) -> List[Tuple[ChatSession, User]]:
        """
        Возвращает список кортежей (сессия, собеседник) для всех активных чатов пользователя.
        """
        stmt = select(ChatSession).where(
            or_(ChatSession.user_a_id == user_id, ChatSession.user_b_id == user_id),
            ChatSession.status == "active"
        ).order_by(ChatSession.created_at.desc())
        res = await session.execute(stmt)
        chats = res.scalars().all()

        result = []
        for c in chats:
            partner_id = c.user_b_id if c.user_a_id == user_id else c.user_a_id
            partner = await session.get(User, partner_id)
            if partner:
                result.append((c, partner))
        return result

    @staticmethod
    async def record_relayed_message(
        session: AsyncSession,
        session_id: int,
        sender_id: int,
        sender_message_id: int,
        recipient_message_id: int,
        text: Optional[str] = None,
        media_type: Optional[str] = "text"
    ) -> ChatMessage:
        msg = ChatMessage(
            session_id=session_id,
            sender_id=sender_id,
            sender_message_id=sender_message_id,
            recipient_message_id=recipient_message_id,
            text=text,
            media_type=media_type,
            created_at=utc_now()
        )
        session.add(msg)
        await session.commit()
        return msg

    @staticmethod
    async def get_recent_messages(
        session: AsyncSession,
        session_id: int,
        limit: int = 15
    ) -> List[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        res = await session.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def burn_and_close_chat(
        bot: Bot,
        session: AsyncSession,
        session_id: int,
        closed_by_user_id: int
    ) -> Tuple[bool, Optional[User], Optional[User]]:
        """
        Полное уничтожение чата:
        1. Удаляет все сообщения и файлы из обоих диалогов в Telegram.
        2. Удаляет записи сообщений из БД.
        3. Закрывает сессию чата.
        4. Сбрасывает active_chat_id у пользователей.
        Возвращает (success, user_a, user_b).
        """
        chat = await session.get(ChatSession, session_id)
        if not chat or chat.status != "active":
            return False, None, None

        user_a = await session.get(User, chat.user_a_id)
        user_b = await session.get(User, chat.user_b_id)

        # Извлекаем все сохранённые сообщения
        stmt = select(ChatMessage).where(ChatMessage.session_id == session_id)
        res = await session.execute(stmt)
        messages = res.scalars().all()

        # Удаляем сообщения из обоих чатов в Telegram
        for m in messages:
            sender_user = user_a if m.sender_id == chat.user_a_id else user_b
            recipient_user = user_b if m.sender_id == chat.user_a_id else user_a

            if sender_user and m.sender_message_id:
                try:
                    await bot.delete_message(chat_id=sender_user.telegram_id, message_id=m.sender_message_id)
                except Exception:
                    pass

            if recipient_user and m.recipient_message_id:
                try:
                    await bot.delete_message(chat_id=recipient_user.telegram_id, message_id=m.recipient_message_id)
                except Exception:
                    pass

        # Удаляем сообщения из БД
        await session.execute(delete(ChatMessage).where(ChatMessage.session_id == session_id))

        # Обновляем статус сессии
        chat.status = "closed"
        chat.closed_at = utc_now()

        # Сбрасываем active_chat_id у обоих участников
        if user_a and user_a.active_chat_id == session_id:
            user_a.active_chat_id = None
        if user_b and user_b.active_chat_id == session_id:
            user_b.active_chat_id = None

        await session.commit()
        return True, user_a, user_b

    @staticmethod
    def get_partner_id(chat: ChatSession, current_user_id: int) -> int:
        return chat.user_b_id if chat.user_a_id == current_user_id else chat.user_a_id
