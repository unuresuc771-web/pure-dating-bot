from typing import Optional, Tuple, List
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, Reaction, Match, utc_now

class MatchingService:
    @staticmethod
    async def get_next_profile(session: AsyncSession, viewer: User) -> Optional[Tuple[User, Optional[str]]]:
        """
        Ищет следующую анкету:
        1. В первую очередь тех, кто уже поставил лайк зрителю.
        2. Затем тех, кто в том же городе.
        3. Затем остальных по совместимости.
        """
        reacted_subquery = (
            select(Reaction.to_user_id)
            .where(Reaction.from_user_id == viewer.id)
            .scalar_subquery()
        )

        base_conditions = [
            User.id != viewer.id,
            User.is_active.is_(True),
            User.is_banned.is_(False),
            User.id.not_in(reacted_subquery)
        ]

        # Фильтр по полу / типу анкеты
        if viewer.target_gender in ("male", "female", "couple"):
            base_conditions.append(User.gender == viewer.target_gender)

        # Кандидат также должен быть заинтересован в поле зрителя
        base_conditions.append(
            or_(
                User.target_gender == viewer.gender,
                User.target_gender == "all"
            )
        )

        # Фильтр по возрасту
        age_min = viewer.search_age_min if viewer.search_age_min is not None else 18
        age_max = viewer.search_age_max if viewer.search_age_max is not None else 99
        base_conditions.append(User.age >= age_min)
        base_conditions.append(User.age <= age_max)

        # 1. Проверяем входящие лайки (приоритет №1, сначала реальные)
        incoming_likes_query = (
            select(User, Reaction.message)
            .join(Reaction, Reaction.from_user_id == User.id)
            .where(
                and_(
                    Reaction.to_user_id == viewer.id,
                    Reaction.reaction_type == "like",
                    *base_conditions
                )
            )
            .order_by(User.is_fake.asc(), Reaction.created_at.asc())
            .limit(1)
        )
        res = await session.execute(incoming_likes_query)
        incoming_pair = res.first()
        if incoming_pair:
            return incoming_pair[0], incoming_pair[1]

        # 2. Поиск по городу (сначала реальные, потом виртуальные)
        has_specific_city = bool(
            viewer.search_city and viewer.search_city.strip() and viewer.search_city.strip().lower() not in ("любой", "все", "all")
        )

        if has_specific_city:
            target_city = viewer.search_city.strip()
            city_query = (
                select(User)
                .where(
                    and_(
                        func.lower(User.city) == func.lower(target_city),
                        *base_conditions
                    )
                )
                .order_by(User.is_fake.asc(), func.random())
                .limit(1)
            )
            city_res = await session.execute(city_query)
            candidate = city_res.scalar_one_or_none()
            if candidate:
                return candidate, None
            return None

        # Если город не зафиксирован: сначала в том же городе, затем везде (всегда реальные первыми)
        same_city_query = (
            select(User)
            .where(
                and_(
                    func.lower(User.city) == func.lower(viewer.city),
                    *base_conditions
                )
            )
            .order_by(User.is_fake.asc(), func.random())
            .limit(1)
        )
        same_city_res = await session.execute(same_city_query)
        candidate = same_city_res.scalar_one_or_none()
        if candidate:
            return candidate, None

        # 3. Ищем в любых городах (реальные первыми)
        general_query = (
            select(User)
            .where(and_(*base_conditions))
            .order_by(User.is_fake.asc(), func.random())
            .limit(1)
        )
        general_res = await session.execute(general_query)
        candidate = general_res.scalar_one_or_none()
        if candidate:
            return candidate, None

        return None

    @staticmethod
    async def get_incoming_likes(session: AsyncSession, user_id: int) -> List[Tuple[User, Optional[str]]]:
        """
        Возвращает пользователей, которые поставили лайк, но на которых еще не ответили.
        """
        reacted_subquery = (
            select(Reaction.to_user_id)
            .where(Reaction.from_user_id == user_id)
            .scalar_subquery()
        )

        query = (
            select(User, Reaction.message)
            .join(Reaction, Reaction.from_user_id == User.id)
            .where(
                Reaction.to_user_id == user_id,
                Reaction.reaction_type == "like",
                User.id.not_in(reacted_subquery),
                User.is_active.is_(True),
                User.is_banned.is_(False)
            )
            .order_by(Reaction.created_at.desc())
        )
        res = await session.execute(query)
        return res.all()

    @staticmethod
    async def record_reaction(
        session: AsyncSession,
        from_user: User,
        target_user_id: int,
        reaction_type: str,
        message: Optional[str] = None
    ) -> Tuple[bool, Optional[User]]:
        target_user = await session.get(User, target_user_id)
        if not target_user:
            return False, None

        stmt = select(Reaction).where(
            Reaction.from_user_id == from_user.id,
            Reaction.to_user_id == target_user_id
        )
        res = await session.execute(stmt)
        reaction = res.scalar_one_or_none()

        if reaction:
            reaction.reaction_type = reaction_type
            reaction.message = message
            reaction.created_at = utc_now()
        else:
            reaction = Reaction(
                from_user_id=from_user.id,
                to_user_id=target_user_id,
                reaction_type=reaction_type,
                message=message,
                created_at=utc_now()
            )
            session.add(reaction)

        is_match = False
        if reaction_type == "like":
            back_stmt = select(Reaction).where(
                Reaction.from_user_id == target_user_id,
                Reaction.to_user_id == from_user.id,
                Reaction.reaction_type == "like"
            )
            back_res = await session.execute(back_stmt)
            if back_res.scalar_one_or_none():
                is_match = True
                u1 = min(from_user.id, target_user_id)
                u2 = max(from_user.id, target_user_id)
                m_check = await session.execute(
                    select(Match).where(Match.user1_id == u1, Match.user2_id == u2)
                )
                if not m_check.scalar_one_or_none():
                    session.add(Match(user1_id=u1, user2_id=u2, created_at=utc_now()))

        await session.commit()
        return is_match, target_user
