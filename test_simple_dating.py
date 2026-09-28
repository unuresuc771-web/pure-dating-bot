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
from bot.database.models import Base, get_random_default_avatar
from bot.services.user_service import UserService
from bot.services.matching import MatchingService

async def run_tests():
    print("🧪 Starting Simple Dating Bot Automated Tests...")

    # 1. Пересоздаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables initialized.")

    # 2. Проверяем наличие всех 20 мужских и 20 женских аватаров на диске
    for i in range(1, 21):
        m_path = os.path.join("assets", "avatars", "male", f"male_{i:02d}.jpg")
        f_path = os.path.join("assets", "avatars", "female", f"female_{i:02d}.jpg")
        assert os.path.exists(m_path), f"Male avatar {m_path} missing!"
        assert os.path.exists(f_path), f"Female avatar {f_path} missing!"
    
    from bot.constants import get_random_pure_nickname
    m_nick = get_random_pure_nickname("male")
    f_nick = get_random_pure_nickname("female")
    assert len(m_nick) > 0 and len(f_nick) > 0
    print(f"✅ Verified all 40 Pure-style avatars on disk and nicknames: '{m_nick}' & '{f_nick}'")
    male_avatar = get_random_default_avatar("male")
    female_avatar = get_random_default_avatar("female")

    async with async_session_maker() as session:
        # 3. Создаем пользователей с автоматическими аватарами
        u1 = await UserService.create_user(
            session=session,
            telegram_id=111111,
            username="alex_tg",
            first_name="Алексей",
            gender="male",
            target_gender="female",
            age=25,
            city="Москва",
            bio="Люблю кофе и вечерние прогулки ☕️",
            avatar_path=male_avatar,
            is_custom_photo=False
        )

        u2 = await UserService.create_user(
            session=session,
            telegram_id=222222,
            username="daria_tg",
            first_name="Дарья",
            gender="female",
            target_gender="male",
            age=23,
            city="Москва",
            bio="Дизайн, музыка и искреннее общение ✨",
            avatar_path=female_avatar,
            is_custom_photo=False
        )
        print(f"✅ Users created: {u1.first_name} and {u2.first_name}")

        # 4. Алексей ищет анкеты -> находит Дарью
        cand_pair = await MatchingService.get_next_profile(session, u1)
        assert cand_pair is not None
        cand, msg = cand_pair
        assert cand.id == u2.id
        print(f"✅ Discovery verified: Alex found {cand.first_name} in {cand.city}")

        # 5. Алексей ставит лайк с сообщением
        is_match, target = await MatchingService.record_reaction(
            session=session,
            from_user=u1,
            target_user_id=u2.id,
            reaction_type="like",
            message="Привет! Классный аватар :)"
        )
        assert not is_match, "First like is not a match yet"
        print(f"✅ Alex liked {target.first_name} with message.")

        # 6. Дарья проверяет раздел «Кому я нравлюсь»
        incoming = await MatchingService.get_incoming_likes(session, u2.id)
        assert len(incoming) == 1
        sender, inc_msg = incoming[0]
        assert sender.id == u1.id
        assert inc_msg == "Привет! Классный аватар :)"
        print(f"✅ 'Кому я нравлюсь' verified: Daria sees Alex with message: '{inc_msg}'")

        # 7. Дарья отвечает взаимным лайком -> МЭТЧ!
        is_match_2, target_2 = await MatchingService.record_reaction(
            session=session,
            from_user=u2,
            target_user_id=u1.id,
            reaction_type="like"
        )
        assert is_match_2, "Mutual like MUST trigger mutual match!"
        print(f"🎉 Mutual match verified! Alex <-> {target_2.first_name}")

        # 8. Проверка форматирования карточки профиля
        caption = UserService.format_caption(u1, is_owner=True)
        assert "Алексей" in caption
        assert "Москва" in caption
        print("✅ Caption formatting verified.")

        # 9. Проверка смены аватара
        new_male_avatar = get_random_default_avatar("male")
        await UserService.update_user(session, u1.id, avatar_path=new_male_avatar)
        updated_u1 = await UserService.get_by_id(session, u1.id)
        assert updated_u1.avatar_path == new_male_avatar
        print("✅ Avatar shuffle verified.")

    await engine.dispose()
    print("\n🌟 ALL TESTS PASSED SUCCESSFULLY! 🌟\n")

if __name__ == "__main__":
    asyncio.run(run_tests())
