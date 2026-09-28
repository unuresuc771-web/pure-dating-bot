from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import (
    User, ChatSession, ChatMessage, SecretMedia, Reaction, Match, Report,
    SystemSetting, UserVisit, utc_now, ensure_utc
)
from bot.config import settings

class AdminService:
    DEFAULT_ACCESS_PASSWORD = "pure2026"
    DEFAULT_ADMIN_PASSWORD = "pureadmin2026"

    @staticmethod
    def is_admin_id(telegram_id: int) -> bool:
        return telegram_id in settings.admin_list

    @staticmethod
    async def get_setting(session: AsyncSession, key: str, default: str = "") -> str:
        stmt = select(SystemSetting).where(SystemSetting.key == key)
        res = await session.execute(stmt)
        setting = res.scalar_one_or_none()
        return setting.value if setting else default

    @staticmethod
    async def set_setting(session: AsyncSession, key: str, value: str):
        stmt = select(SystemSetting).where(SystemSetting.key == key)
        res = await session.execute(stmt)
        setting = res.scalar_one_or_none()
        if setting:
            setting.value = value
            setting.updated_at = utc_now()
        else:
            setting = SystemSetting(key=key, value=value, updated_at=utc_now())
            session.add(setting)
        await session.commit()

    @staticmethod
    async def is_password_protection_enabled(session: AsyncSession) -> bool:
        val = await AdminService.get_setting(session, "access_password_enabled", "0")
        return val == "1"

    @staticmethod
    async def get_access_password(session: AsyncSession) -> str:
        return await AdminService.get_setting(session, "access_password", AdminService.DEFAULT_ACCESS_PASSWORD)

    @staticmethod
    async def get_virtual_match_rate(session: AsyncSession) -> float:
        val = await AdminService.get_setting(session, "virtual_match_rate", "0.20")
        try:
            return float(val)
        except ValueError:
            return 0.20

    @staticmethod
    async def set_virtual_match_rate(session: AsyncSession, rate: float):
        await AdminService.set_setting(session, "virtual_match_rate", str(rate))

    @staticmethod
    async def is_user_authorized_for_gate(session: AsyncSession, telegram_id: int) -> bool:
        from bot.database.models import AuthorizedAccess
        stmt = select(AuthorizedAccess).where(AuthorizedAccess.telegram_id == telegram_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none() is not None

    @staticmethod
    async def authorize_user_for_gate(session: AsyncSession, telegram_id: int):
        from bot.database.models import AuthorizedAccess
        stmt = select(AuthorizedAccess).where(AuthorizedAccess.telegram_id == telegram_id)
        res = await session.execute(stmt)
        if not res.scalar_one_or_none():
            entry = AuthorizedAccess(telegram_id=telegram_id, authorized_at=utc_now())
            session.add(entry)
            await session.commit()

    @staticmethod
    async def verify_admin_password(session: AsyncSession, password: str) -> bool:
        stored = await AdminService.get_setting(session, "admin_password", AdminService.DEFAULT_ADMIN_PASSWORD)
        return password.strip() == stored.strip()

    @staticmethod
    async def record_user_activity(session: AsyncSession, user_id: int):
        now = utc_now()
        # 1. Update user last_seen_at
        user_stmt = select(User).where(User.id == user_id)
        user_res = await session.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        if not user:
            return
        user.last_seen_at = now

        # 2. Check latest UserVisit
        visit_stmt = (
            select(UserVisit)
            .where(UserVisit.user_id == user_id)
            .order_by(UserVisit.last_action_at.desc())
            .limit(1)
        )
        visit_res = await session.execute(visit_stmt)
        latest_visit = visit_res.scalar_one_or_none()

        last_action = ensure_utc(latest_visit.last_action_at) if latest_visit else None
        gap_seconds = (now - last_action).total_seconds() if last_action else 999999

        if latest_visit and gap_seconds < 900:  # 15 minutes window
            latest_visit.actions_count += 1
            latest_visit.last_action_at = now
            started_at = ensure_utc(latest_visit.started_at) or now
            duration = int((now - started_at).total_seconds())
            delta = duration - (latest_visit.duration_seconds or 0)
            latest_visit.duration_seconds = duration
            if delta > 0:
                user.total_active_seconds = (user.total_active_seconds or 0) + delta
        else:
            # New visit session
            new_visit = UserVisit(
                user_id=user_id,
                started_at=now,
                last_action_at=now,
                actions_count=1,
                duration_seconds=0
            )
            session.add(new_visit)

        await session.commit()

    @staticmethod
    async def get_analytics_summary(session: AsyncSession) -> Dict[str, Any]:
        now = utc_now()
        t_15m = now - timedelta(minutes=15)
        t_24h = now - timedelta(hours=24)
        t_7d = now - timedelta(days=7)
        t_30d = now - timedelta(days=30)

        # 1. Users count (total, real, fake)
        total_users = (await session.execute(select(func.count(User.id)))).scalar() or 0
        real_users = (await session.execute(select(func.count(User.id)).where(User.is_fake.is_(False)))).scalar() or 0
        fake_users = (await session.execute(select(func.count(User.id)).where(User.is_fake.is_(True)))).scalar() or 0

        # Genders (Real)
        real_male = (await session.execute(select(func.count(User.id)).where(User.is_fake.is_(False), User.gender == "male"))).scalar() or 0
        real_female = (await session.execute(select(func.count(User.id)).where(User.is_fake.is_(False), User.gender == "female"))).scalar() or 0
        real_couple = (await session.execute(select(func.count(User.id)).where(User.is_fake.is_(False), User.gender == "couple"))).scalar() or 0

        # Genders (Fake)
        fake_male = (await session.execute(select(func.count(User.id)).where(User.is_fake.is_(True), User.gender == "male"))).scalar() or 0
        fake_female = (await session.execute(select(func.count(User.id)).where(User.is_fake.is_(True), User.gender == "female"))).scalar() or 0
        fake_couple = (await session.execute(select(func.count(User.id)).where(User.is_fake.is_(True), User.gender == "couple"))).scalar() or 0

        # 2. Activity metrics
        online_now = (await session.execute(select(func.count(User.id)).where(User.is_fake.is_(False), User.last_seen_at >= t_15m))).scalar() or 0
        dau = (await session.execute(select(func.count(User.id)).where(User.is_fake.is_(False), User.last_seen_at >= t_24h))).scalar() or 0
        wau = (await session.execute(select(func.count(User.id)).where(User.is_fake.is_(False), User.last_seen_at >= t_7d))).scalar() or 0
        mau = (await session.execute(select(func.count(User.id)).where(User.is_fake.is_(False), User.last_seen_at >= t_30d))).scalar() or 0

        new_24h = (await session.execute(select(func.count(User.id)).where(User.is_fake.is_(False), User.created_at >= t_24h))).scalar() or 0
        new_7d = (await session.execute(select(func.count(User.id)).where(User.is_fake.is_(False), User.created_at >= t_7d))).scalar() or 0

        # Average duration from UserVisit
        avg_visit_sec = (await session.execute(select(func.avg(UserVisit.duration_seconds)).where(UserVisit.duration_seconds > 0))).scalar() or 0
        total_visits = (await session.execute(select(func.count(UserVisit.id)))).scalar() or 0

        # 3. Chats and messages
        total_chats = (await session.execute(select(func.count(ChatSession.id)))).scalar() or 0
        active_chats = (await session.execute(select(func.count(ChatSession.id)).where(ChatSession.status == "active"))).scalar() or 0
        total_msgs = (await session.execute(select(func.count(ChatMessage.id)))).scalar() or 0
        msgs_24h = (await session.execute(select(func.count(ChatMessage.id)).where(ChatMessage.created_at >= t_24h))).scalar() or 0
        
        # Secret photos
        total_secrets = (await session.execute(select(func.count(SecretMedia.id)))).scalar() or 0
        viewed_secrets = (await session.execute(select(func.count(SecretMedia.id)).where(SecretMedia.is_viewed.is_(True)))).scalar() or 0

        # 4. Likes & Matches
        total_likes = (await session.execute(select(func.count(Reaction.id)).where(Reaction.reaction_type == "like"))).scalar() or 0
        total_matches = (await session.execute(select(func.count(Match.id)))).scalar() or 0
        match_rate = round((total_matches * 2 / total_likes * 100), 1) if total_likes > 0 else 0.0

        # 5. Reports & Bans
        total_reports = (await session.execute(select(func.count(Report.id)))).scalar() or 0
        banned_users = (await session.execute(select(func.count(User.id)).where(User.is_banned.is_(True)))).scalar() or 0

        # Password status
        pass_enabled = await AdminService.is_password_protection_enabled(session)
        pass_val = await AdminService.get_access_password(session)

        return {
            "total_users": total_users,
            "real_users": real_users,
            "fake_users": fake_users,
            "real_male": real_male,
            "real_female": real_female,
            "real_couple": real_couple,
            "fake_male": fake_male,
            "fake_female": fake_female,
            "fake_couple": fake_couple,
            "online_now": online_now,
            "dau": dau,
            "wau": wau,
            "mau": mau,
            "new_24h": new_24h,
            "new_7d": new_7d,
            "avg_visit_min": round(avg_visit_sec / 60, 1),
            "total_visits": total_visits,
            "total_chats": total_chats,
            "active_chats": active_chats,
            "total_msgs": total_msgs,
            "msgs_24h": msgs_24h,
            "total_secrets": total_secrets,
            "viewed_secrets": viewed_secrets,
            "total_likes": total_likes,
            "total_matches": total_matches,
            "match_rate": match_rate,
            "total_reports": total_reports,
            "banned_users": banned_users,
            "pass_enabled": pass_enabled,
            "pass_val": pass_val,
        }
