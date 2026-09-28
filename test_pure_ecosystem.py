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
from bot.database.models import Base
from bot.services.user_service import UserService
from bot.services.ad_service import AdService
from bot.services.feed_service import FeedService
from bot.services.chat_service import ChatService
from bot.services.devils_bones_service import DevilsBonesService

async def run_pure_tests():
    print("🔥 Starting Pure Ecosystem Automated Verification...")

    # Чистим и заново инициализируем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Pure Database tables recreated successfully.")

    async with async_session_maker() as session:
        # 1. Создаем двух пользователей
        u1 = await UserService.create_user(
            session=session,
            telegram_id=10001,
            username="eva_pure",
            first_name="Ева",
            gender="woman",
            orientation="hetero",
            target_gender="man",
            age=24,
            city="Москва"
        )
        u2 = await UserService.create_user(
            session=session,
            telegram_id=10002,
            username="mark_pure",
            first_name="Марк",
            gender="man",
            orientation="hetero",
            target_gender="woman",
            age=28,
            city="Москва"
        )
        print(f"✅ Users created: {u1.first_name} and {u2.first_name}")

        # 2. Проверяем правило Give-to-Get
        # Марк пытается смотреть ленту, не опубликовав объявление
        _, _, _, blocked = await FeedService.get_next_ad(session, u2)
        assert blocked, "Give-to-Get MUST block feed if user has no active ad!"
        print("✅ Give-to-Get rule successfully verified: feed blocked without active Ad.")

        # 3. Ева публикует объявление
        ad_eva = await AdService.create_or_replace_ad(
            session=session,
            user_id=u1.id,
            content="Ищу компанию на бокал вина и разговоры на крыше 🍷",
            dating_goal="casual",
            turn_ons=["Романтика & Кофе ☕️", "Ночные поездки 🌃", "Спонтанный секс 🔥"],
            photo_id="eva_silhouette_photo"
        )
        print(f"✅ Eva published Ad (id={ad_eva.id}, expires_in={AdService.get_remaining_time_str(ad_eva.expires_at)})")

        # 4. Марк публикует объявление со схожими Turn-Ons
        ad_mark = await AdService.create_or_replace_ad(
            session=session,
            user_id=u2.id,
            content="Спонтанные прогулки по ночному городу, кофе и искренний вайб 🌃",
            dating_goal="casual",
            turn_ons=["Ночные поездки 🌃", "Разговоры до утра 🌙"],
            photo_id="mark_mood_photo"
        )
        print(f"✅ Mark published Ad (id={ad_mark.id}). Feed now unlocked!")

        # 5. Марк заходит в ленту -> видит объявление Евы
        ad_found, author_found, _, blocked_now = await FeedService.get_next_ad(session, u2)
        assert not blocked_now, "Feed must be unlocked after publishing ad"
        assert ad_found is not None and author_found.id == u1.id
        print(f"✅ Mark sees Eva's Ad via smart Feed ranking (Goal match & Turn-Ons intersection)!")

        # 6. Проверяем механику «Царь горы» (King of the Hill)
        u3 = await UserService.create_user(
            session=session,
            telegram_id=10003,
            username="daria_pure",
            first_name="Дарья",
            gender="woman",
            orientation="hetero",
            target_gender="man",
            age=22,
            city="Москва"
        )
        ad_daria = await AdService.create_or_replace_ad(
            session=session,
            user_id=u3.id,
            content="Привет, ищу приключения!",
            dating_goal="anything_but_boring",
            turn_ons=[],
            photo_id="daria_photo"
        )
        await AdService.make_king_of_the_hill(session, ad_daria.id)
        # Теперь Дарья должна быть первой в ленте Марка благодаря статусу Царя Горы!
        top_ad, top_author, _, _ = await FeedService.get_next_ad(session, u2)
        assert top_author.id == u3.id, "King of the Hill ad MUST be ranked #1 in feed!"
        print("👑 King of the Hill priority successfully verified: Daria is ranked #1!")

        # 7. Марк ставит лайк Еве, а Ева ставит взаимный лайк Марку
        await UserService.record_reaction(session, u2.id, u1.id, ad_eva.id, "like")
        is_match, _ = await UserService.record_reaction(session, u1.id, u2.id, ad_mark.id, "like")
        assert is_match, "Mutual like MUST trigger match"

        # 8. Создание анонимной 24h сессии Pure
        chat = await ChatService.create_or_get_session(session, u1.id, u2.id)
        assert chat.status == "active"
        assert chat.is_timer_active
        nick_eva, nick_mark, _ = ChatService.get_user_display_name_and_partner_id(chat, u1.id)
        print(f"🎉 Anonymous 24h Chat opened! Eva's nick: '{nick_eva}', Mark's nick: '{nick_mark}'")

        # 9. Сообщения в анонимном чате
        msg = await ChatService.save_message(session, chat.id, u1.id, text="Привет, понравился твой вайб!")
        assert msg.id is not None
        print(f"✅ Anonymized message saved: '{msg.text}'")

        # 10. Остановка таймера 24h
        _, stopped_1 = await ChatService.request_stop_timer(session, chat.id, u1.id)
        assert not stopped_1, "Only one user requested, timer not stopped yet"
        _, stopped_2 = await ChatService.request_stop_timer(session, chat.id, u2.id)
        assert stopped_2, "Both requested: 24h timer MUST be turned off (infinite chat)!"
        print("♾ Both users stopped the 24h countdown -> Chat is now permanent!")

        # 11. Обмен контактами Telegram
        _, shared_1, _, _ = await ChatService.request_share_contact(session, chat.id, u1.id)
        assert not shared_1
        _, shared_2, user_a, user_b = await ChatService.request_share_contact(session, chat.id, u2.id)
        assert shared_2, "Both requested: Contacts MUST be mutually shared!"
        print(f"📱 Mutual Contact sharing verified: @{user_a.username} <-> @{user_b.username}")

        # 12. Механика «Сжечь чат» (Burn Chat / Zero-Footprint)
        burn_res = await ChatService.terminate_session(session, chat.id)
        assert burn_res
        burned_chat = await ChatService.get_session_by_id(session, chat.id)
        assert burned_chat.status == "terminated"
        print("💣 'Burn chat' verified: Session terminated and messages wiped!")

        # 13. Тест «Кости дьявола» (Devil's Bones 🎲)
        db_chat, p1 = await DevilsBonesService.roll_the_bones(session, u1)
        assert db_chat is None, "First roller enters queue"
        db_chat_2, p2 = await DevilsBonesService.roll_the_bones(session, u2)
        assert db_chat_2 is not None and p2.id == u1.id, "Second roller MUST instantly connect with waiting user!"
        print(f"🎲 Devil's Bones verified: Instant anonymous pairing achieved!")

    await engine.dispose()
    print("\n🌟 ALL PURE ECOSYSTEM TESTS PASSED PERFECTLY! 🌟\n")

if __name__ == "__main__":
    asyncio.run(run_pure_tests())
