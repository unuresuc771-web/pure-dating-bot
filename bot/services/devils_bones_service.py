from typing import Optional, Tuple
from sqlalchemy import select, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, DevilsBonesQueue, ChatSession, utc_now
from bot.services.chat_service import ChatService

class DevilsBonesService:
    @staticmethod
    async def roll_the_bones(session: AsyncSession, current_user: User) -> Tuple[Optional[ChatSession], Optional[User]]:
        """
        Бросок костей дьявола:
        Ищет случайного собеседника в очереди.
        Если находит — моментально запускает анонимный чат и удаляет из очереди.
        Если нет — ставит в очередь ожидания.
        """
        # Удаляем старые записи текущего пользователя из очереди, если были
        await session.execute(
            delete(DevilsBonesQueue).where(DevilsBonesQueue.user_id == current_user.id)
        )

        # Ищем подходящего партнера из очереди
        query = (
            select(DevilsBonesQueue, User)
            .join(User, DevilsBonesQueue.user_id == User.id)
            .where(
                DevilsBonesQueue.user_id != current_user.id,
                User.is_banned.is_(False)
            )
            .order_by(DevilsBonesQueue.joined_at.asc())
            .limit(1)
        )
        res = await session.execute(query)
        match_candidate = res.first()

        if match_candidate:
            queue_item, partner = match_candidate
            # Удаляем партнера из очереди
            await session.delete(queue_item)
            await session.commit()

            # Создаем анонимную сессию
            chat_session = await ChatService.create_or_get_session(
                session=session,
                user_a_id=current_user.id,
                user_b_id=partner.id
            )
            return chat_session, partner
        else:
            # Никого нет, встаем в очередь
            new_entry = DevilsBonesQueue(user_id=current_user.id, joined_at=utc_now())
            session.add(new_entry)
            await session.commit()
            return None, None

    @staticmethod
    async def leave_queue(session: AsyncSession, user_id: int):
        await session.execute(
            delete(DevilsBonesQueue).where(DevilsBonesQueue.user_id == user_id)
        )
        await session.commit()
