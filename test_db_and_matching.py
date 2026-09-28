import asyncio
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
from bot.database.db import init_db, async_session_maker, engine
from bot.services.user_service import UserService
from bot.services.matching import MatchingService

async def run_tests():
    print("🧪 Starting Automated Verification of Dating Bot Logic...")

    # 1. Init DB
    await init_db()
    print("✅ Database initialized successfully.")

    async with async_session_maker() as session:
        # 2. Create Test Users
        u1 = await UserService.create_user(
            session=session,
            telegram_id=11111111,
            username="anna_test",
            name="Анна",
            gender="female",
            age=23,
            city="Москва",
            target_gender="male",
            bio="Люблю дизайн, путешествия и театр 🎭",
            photo_id="test_photo_id_anna"
        )
        print(f"✅ User 1 created: {u1.name} (id={u1.id})")

        u2 = await UserService.create_user(
            session=session,
            telegram_id=22222222,
            username="boris_test",
            name="Борис",
            gender="male",
            age=26,
            city="Москва",
            target_gender="female",
            bio="Backend разработчик, спорт, кофе ☕️",
            photo_id="test_photo_id_boris"
        )
        print(f"✅ User 2 created: {u2.name} (id={u2.id})")

        u3 = await UserService.create_user(
            session=session,
            telegram_id=33333333,
            username=None,
            name="Ольга",
            gender="female",
            age=25,
            city="Москва",
            target_gender="male",
            bio="Фотография и прогулки по паркам 📸",
            photo_id="test_photo_id_olga"
        )
        print(f"✅ User 3 created: {u3.name} (id={u3.id})")

        # 3. Test Boris searching
        candidate_pair = await MatchingService.get_next_candidate(session, u2)
        assert candidate_pair is not None, "Candidate should be found for Boris"
        cand, msg = candidate_pair
        print(f"✅ Boris found candidate: {cand.name} (city={cand.city})")

        # 4. Boris likes Anna with a compliment message
        is_match, target = await MatchingService.record_reaction(
            session=session,
            from_user=u2,
            target_user_id=u1.id,
            reaction_type="like",
            message="Классная улыбка! 🙂"
        )
        assert not is_match, "First like should not be a mutual match yet"
        print(f"✅ Boris liked {target.name} with compliment.")

        # 5. Anna searches -> Boris MUST be first due to incoming like priority!
        anna_cand_pair = await MatchingService.get_next_candidate(session, u1)
        assert anna_cand_pair is not None, "Candidate should be found for Anna"
        anna_cand, anna_compliment = anna_cand_pair
        assert anna_cand.id == u2.id, f"Boris should be prioritized for Anna, got {anna_cand.name}"
        assert anna_compliment == "Классная улыбка! 🙂", f"Compliment should match, got '{anna_compliment}'"
        print(f"✅ Priority matching confirmed: Anna sees {anna_cand.name} first with compliment: '{anna_compliment}'")

        # 6. Anna likes Boris back -> MUTUAL MATCH!
        is_match2, target2 = await MatchingService.record_reaction(
            session=session,
            from_user=u1,
            target_user_id=u2.id,
            reaction_type="like"
        )
        assert is_match2, "Mutual like MUST trigger is_match=True"
        print(f"🎉 Mutual match successfully triggered between {u1.name} and {target2.name}!")

        # 7. Check that Boris does not see Anna again
        boris_cand_2 = await MatchingService.get_next_candidate(session, u2)
        assert boris_cand_2 is not None
        assert boris_cand_2[0].id == u3.id, f"Boris should now see Olga, got {boris_cand_2[0].name}"
        print(f"✅ Boris now sees remaining candidate: {boris_cand_2[0].name}")

        # 8. Test profile editing & caption formatting
        updated_u1 = await UserService.update_user(session, u1.id, city="Санкт-Петербург", age=24)
        assert updated_u1.city == "Санкт-Петербург"
        assert updated_u1.age == 24
        caption = UserService.format_profile_caption(updated_u1, is_owner=True)
        assert "Санкт-Петербург" in caption
        print(f"✅ Profile edit and caption formatting verified.")

        # 9. Test pause / resume
        await UserService.set_active(session, u3.id, is_active=False)
        paused_user = await UserService.get_by_id(session, u3.id)
        assert not paused_user.is_active
        print(f"✅ User pause / active status toggle verified.")

    await engine.dispose()
    print("\n🌟 ALL TESTS PASSED SUCCESSFULLY! 🌟\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
