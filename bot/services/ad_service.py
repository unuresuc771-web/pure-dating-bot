from typing import Optional, List
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, PersonalAd, utc_now, default_ad_expires, ensure_utc
from bot.constants import DATING_GOALS

class AdService:
    @staticmethod
    async def get_active_ad(session: AsyncSession, user_id: int) -> Optional[PersonalAd]:
        stmt = select(PersonalAd).where(
            PersonalAd.user_id == user_id,
            PersonalAd.is_active.is_(True),
            PersonalAd.expires_at > utc_now()
        ).order_by(PersonalAd.created_at.desc()).limit(1)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_any_ad(session: AsyncSession, user_id: int) -> Optional[PersonalAd]:
        stmt = select(PersonalAd).where(
            PersonalAd.user_id == user_id
        ).order_by(PersonalAd.created_at.desc()).limit(1)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def create_or_replace_ad(
        session: AsyncSession,
        user_id: int,
        content: str,
        dating_goal: str,
        turn_ons: List[str],
        photo_id: str
    ) -> PersonalAd:
        # Деактивируем предыдущие объявления
        await session.execute(
            update(PersonalAd).where(PersonalAd.user_id == user_id).values(is_active=False)
        )

        ad = PersonalAd(
            user_id=user_id,
            content=content,
            dating_goal=dating_goal,
            photo_id=photo_id,
            expires_at=default_ad_expires(),
            is_active=True
        )
        ad.turn_ons = turn_ons
        session.add(ad)
        await session.commit()
        await session.refresh(ad)
        return ad

    @staticmethod
    async def refresh_timer(session: AsyncSession, ad_id: int) -> PersonalAd:
        ad = await session.get(PersonalAd, ad_id)
        if ad:
            ad.expires_at = default_ad_expires()
            ad.is_active = True
            ad.updated_at = utc_now()
            await session.commit()
            await session.refresh(ad)
        return ad

    @staticmethod
    async def make_king_of_the_hill(session: AsyncSession, ad_id: int) -> PersonalAd:
        ad = await session.get(PersonalAd, ad_id)
        if ad:
            ad.is_king_of_the_hill = True
            ad.king_expires_at = utc_now() + timedelta(hours=1)
            ad.updated_at = utc_now()
            await session.commit()
            await session.refresh(ad)
        return ad

    @staticmethod
    def get_remaining_time_str(expires_at: datetime) -> str:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        diff = expires_at - utc_now()
        if diff.total_seconds() <= 0:
            return "Время истекло"
        hours, remainder = divmod(int(diff.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}ч {minutes}м"

    @staticmethod
    def format_ad_caption(ad: PersonalAd, author: User, is_owner: bool = False) -> str:
        goal_text = DATING_GOALS.get(ad.dating_goal, ad.dating_goal)
        turn_ons_formatted = " • ".join(ad.turn_ons) if ad.turn_ons else "Не указано"
        king_badge = "👑 <b>ЦАРЬ ГОРЫ</b>\n" if (ad.is_king_of_the_hill and ad.king_expires_at and ensure_utc(ad.king_expires_at) > utc_now()) else ""

        gender_map = {"man": "Мужчина", "woman": "Девушка", "non_binary": "Небинарный"}
        author_gender = gender_map.get(author.gender, author.gender)

        time_left = AdService.get_remaining_time_str(ad.expires_at)

        if is_owner:
            return (
                f"{king_badge}"
                f"📝 <b>Ваше объявление в Pure</b>\n\n"
                f"💬 <i>«{ad.content}»</i>\n\n"
                f"🎯 <b>Цель:</b> {goal_text}\n"
                f"✨ <b>Turn-Ons:</b> {turn_ons_formatted}\n"
                f"📍 <b>Локация:</b> {author.city} ({author_gender}, {author.age})\n\n"
                f"⏳ <b>Осталось жить объявлению:</b> {time_left}"
            )
        else:
            return (
                f"{king_badge}"
                f"💬 <i>«{ad.content}»</i>\n\n"
                f"🎯 <b>Цель:</b> {goal_text}\n"
                f"✨ <b>Turn-Ons:</b> {turn_ons_formatted}\n"
                f"📍 <b>Локация:</b> {author.city} ({author_gender}, {author.age})"
            )
