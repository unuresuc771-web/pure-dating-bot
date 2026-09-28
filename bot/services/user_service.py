import os
from typing import Optional
from aiogram import Bot
from sqlalchemy import select, update, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, Report, Reaction, Match, ChatSession, ChatMessage, SecretMedia, utc_now

class UserService:
    @staticmethod
    async def get_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
        stmt = select(User).where(User.telegram_id == telegram_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.id == user_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def create_user(
        session: AsyncSession,
        telegram_id: int,
        username: Optional[str],
        first_name: str,
        gender: str,
        target_gender: str,
        age: int,
        city: str,
        bio: str,
        avatar_path: str,
        is_custom_photo: bool = False,
        search_city: Optional[str] = None,
        search_age_min: int = 18,
        search_age_max: int = 99,
        couple_age: Optional[str] = None,
        is_fake: bool = False,
        referrer_id: Optional[int] = None,
        utm_source: Optional[str] = None
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            gender=gender,
            target_gender=target_gender,
            age=age,
            couple_age=couple_age,
            city=city,
            bio=bio,
            avatar_path=avatar_path,
            is_custom_photo=is_custom_photo,
            search_city=search_city,
            search_age_min=search_age_min,
            search_age_max=search_age_max,
            is_active=True,
            is_banned=False,
            is_fake=is_fake,
            referrer_id=referrer_id,
            utm_source=utm_source
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def update_user(session: AsyncSession, user_id: int, **kwargs) -> Optional[User]:
        kwargs["updated_at"] = utc_now()
        stmt = update(User).where(User.id == user_id).values(**kwargs).returning(User)
        res = await session.execute(stmt)
        await session.commit()
        return res.scalar_one_or_none()

    @staticmethod
    async def set_active(session: AsyncSession, user_id: int, is_active: bool):
        await session.execute(
            update(User).where(User.id == user_id).values(is_active=is_active, updated_at=utc_now())
        )
        await session.commit()

    @staticmethod
    async def set_active_chat(session: AsyncSession, user_id: int, active_chat_id: Optional[int]):
        await session.execute(
            update(User).where(User.id == user_id).values(active_chat_id=active_chat_id, updated_at=utc_now())
        )
        await session.commit()

    @staticmethod
    async def report_user(session: AsyncSession, reporter_id: int, reported_id: int, reason: str):
        rep = Report(reporter_id=reporter_id, reported_user_id=reported_id, reason=reason)
        session.add(rep)
        await session.commit()
        return rep

    @staticmethod
    async def delete_user_completely(bot: Optional[Bot], session: AsyncSession, user_id: int) -> bool:
        """
        Полное и безвозвратное удаление анкеты:
        1. Сжигаются все активные диалоги (сообщения удаляются из Telegram у обоих участников).
        2. Удаляются все сообщения, секретные медиа, чат-сессии, взаимные симпатии, лайки и жалобы.
        3. Удаляются файлы пользовательских аватарок с диска.
        4. Удаляется запись пользователя.
        """
        from bot.services.chat_service import ChatService
        user = await session.get(User, user_id)
        if not user:
            return False

        # 1. Сжигаем все чаты пользователя
        stmt_sessions = select(ChatSession).where(
            or_(ChatSession.user_a_id == user_id, ChatSession.user_b_id == user_id)
        )
        res_sessions = await session.execute(stmt_sessions)
        sessions = res_sessions.scalars().all()

        for s in sessions:
            if bot and s.status == "active":
                try:
                    await ChatService.burn_and_close_chat(bot, session, s.id, user_id)
                except Exception:
                    pass

        # 2. Удаляем связанные данные
        session_ids = [s.id for s in sessions]
        if session_ids:
            await session.execute(delete(SecretMedia).where(SecretMedia.session_id.in_(session_ids)))
            await session.execute(delete(ChatMessage).where(ChatMessage.session_id.in_(session_ids)))
            await session.execute(delete(ChatSession).where(ChatSession.id.in_(session_ids)))

        await session.execute(delete(SecretMedia).where(or_(SecretMedia.sender_id == user_id, SecretMedia.recipient_id == user_id)))
        await session.execute(delete(ChatMessage).where(ChatMessage.sender_id == user_id))
        await session.execute(delete(Match).where(or_(Match.user1_id == user_id, Match.user2_id == user_id)))
        await session.execute(delete(Reaction).where(or_(Reaction.from_user_id == user_id, Reaction.to_user_id == user_id)))
        await session.execute(delete(Report).where(or_(Report.reporter_id == user_id, Report.reported_user_id == user_id)))

        # 3. Удаляем файл фото с диска, если было загружено свое
        if user.is_custom_photo and user.avatar_path and os.path.exists(user.avatar_path):
            try:
                os.remove(user.avatar_path)
            except Exception:
                pass

        # 4. Удаляем самого пользователя
        await session.delete(user)
        await session.commit()
        return True

    @staticmethod
    def format_caption(user: User, is_owner: bool = False) -> str:
        is_couple = (user.gender == "couple")
        if is_couple:
            gender_icon = "👥"
        elif user.gender == "male":
            gender_icon = "👨"
        else:
            gender_icon = "👩"

        target_map = {
            "female": "девушек 👩",
            "male": "парней 👨",
            "couple": "пары 👥",
            "all": "всех 👥"
        }
        target_label = target_map.get(user.target_gender, user.target_gender)

        age_display = user.couple_age if (is_couple and user.couple_age) else str(user.age)
        bio_text = f"\n\n📝 <i>{user.bio}</i>" if user.bio else ""

        if is_owner:
            status_text = "🟢 Видна в поиске" if user.is_active else "⏸ На паузе (скрыта)"
            search_city_label = user.search_city if user.search_city else "Любой"
            age_min = user.search_age_min or 18
            age_max = user.search_age_max or 99
            age_label = "Любой" if age_min <= 18 and age_max >= 90 else f"{age_min}–{age_max}"

            header = "👥 <b>Анкета пары:</b>\n\n" if is_couple else "👤 <b>Ваша анкета:</b>\n\n"
            target_text = f"🎯 Ищем: <b>{target_label}</b>" if is_couple else f"🎯 Ищу: <b>{target_label}</b>"

            return (
                f"{header}"
                f"{gender_icon} <b>{user.first_name}</b>, {age_display}\n"
                f"📍 <b>{user.city}</b>\n"
                f"{target_text}\n"
                f"⚙️ Фильтры: <b>{search_city_label}</b>, возраст <b>{age_label}</b>"
                f"{bio_text}\n\n"
                f"Статус: {status_text}"
            )
        else:
            return (
                f"{gender_icon} <b>{user.first_name}</b>, {age_display}\n"
                f"📍 <b>{user.city}</b>"
                f"{bio_text}"
            )

    @staticmethod
    async def set_personal_password(session: AsyncSession, user_id: int, password: str) -> None:
        user = await UserService.get_by_id(session, user_id)
        if user:
            user.personal_password = password.strip()
            user.updated_at = utc_now()
            await session.commit()

    @staticmethod
    async def remove_personal_password(session: AsyncSession, user_id: int) -> None:
        user = await UserService.get_by_id(session, user_id)
        if user:
            user.personal_password = None
            user.updated_at = utc_now()
            await session.commit()

    @staticmethod
    async def verify_personal_password(session: AsyncSession, user_id: int, password: str) -> bool:
        user = await UserService.get_by_id(session, user_id)
        if not user or not user.personal_password:
            return True
        return user.personal_password.strip().lower() == password.strip().lower()

