from datetime import timezone
from typing import Optional, Tuple, List
from sqlalchemy import select, and_, or_, not_
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, PersonalAd, Reaction, utc_now, ensure_utc
from bot.services.ad_service import AdService

class FeedService:
    @staticmethod
    def calculate_jaccard_similarity(list_a: List[str], list_b: List[str]) -> float:
        set_a, set_b = set(list_a), set(list_b)
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return intersection / union if union > 0 else 0.0

    @staticmethod
    async def get_next_ad(
        session: AsyncSession,
        viewer: User
    ) -> Tuple[Optional[PersonalAd], Optional[User], Optional[str], bool]:
        """
        Возвращает (ad, author, compliment_message, give_to_get_blocked).
        Если give_to_get_blocked = True, значит у зрителя нет активного объявления.
        """
        viewer_ad = await AdService.get_active_ad(session, viewer.id)
        if not viewer_ad:
            return None, None, None, True  # Give-to-Get: лента закрыта!

        # Получаем список ID пользователей, на которых зритель уже реагировал
        reacted_subquery = (
            select(Reaction.to_user_id)
            .where(Reaction.from_user_id == viewer.id)
            .scalar_subquery()
        )

        base_conditions = [
            PersonalAd.user_id != viewer.id,
            PersonalAd.is_active.is_(True),
            PersonalAd.expires_at > utc_now(),
            PersonalAd.user_id.not_in(reacted_subquery),
            User.is_banned.is_(False)
        ]

        # Гендерный фильтр зрителя
        if viewer.target_gender in ("man", "woman"):
            base_conditions.append(User.gender == viewer.target_gender)

        # Гендерный фильтр автора (автор должен искать пол зрителя или "all")
        base_conditions.append(
            or_(
                User.target_gender == viewer.gender,
                User.target_gender == "all"
            )
        )

        stmt = (
            select(PersonalAd, User)
            .join(User, PersonalAd.user_id == User.id)
            .where(and_(*base_conditions))
        )
        res = await session.execute(stmt)
        candidates = res.all()

        if not candidates:
            return None, None, None, False

        # Получаем список пользователей, которые УЖЕ лайкнули зрителя
        incoming_likes_stmt = select(Reaction).where(
            Reaction.to_user_id == viewer.id,
            Reaction.reaction_type.in_(["like", "instant"])
        )
        incoming_res = await session.execute(incoming_likes_stmt)
        incoming_map = {r.from_user_id: r.message for r in incoming_res.scalars().all()}

        # Ранжируем кандидатов по математической формуле Pure
        scored_candidates = []
        viewer_turn_ons = viewer_ad.turn_ons

        for ad, author in candidates:
            score = 0.0

            # 1. King of the Hill (Царь горы)
            if ad.is_king_of_the_hill and ad.king_expires_at and ensure_utc(ad.king_expires_at) > utc_now():
                score += 100.0

            # 2. Входящий лайк / комплимент (приоритет взаимности)
            compliment = incoming_map.get(author.id)
            if author.id in incoming_map:
                score += 50.0

            # 3. Пересечение тегов Turn-Ons (коэффициент Жаккара)
            jaccard = FeedService.calculate_jaccard_similarity(viewer_turn_ons, ad.turn_ons)
            score += jaccard * 30.0

            # 4. Совпадение вектора целей (Dating Goal)
            if ad.dating_goal == viewer_ad.dating_goal:
                score += 20.0

            # 5. Географическая близость (тот же город)
            if author.city.strip().lower() == viewer.city.strip().lower():
                score += 15.0

            # 6. Временная свежесть объявления
            created = ensure_utc(ad.created_at)
            age_hours = (utc_now() - created).total_seconds() / 3600.0
            freshness = max(0.0, 10.0 - (age_hours / 2.4))
            score += freshness

            scored_candidates.append((score, ad, author, compliment))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        best = scored_candidates[0]
        return best[1], best[2], best[3], False
