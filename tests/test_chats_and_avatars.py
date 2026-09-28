import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from bot.database.db import Base
from bot.database.models import User, Reaction, Match, ChatSession, ChatMessage, SecretMedia
from bot.services.user_service import UserService
from bot.services.matching import MatchingService
from bot.services.chat_service import ChatService
from bot.services.avatar_cache import AvatarCacheService

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

async def test_avatar_cache_service():
    test_path = "assets/avatars/male/male_01.jpg"
    test_file_id = "BAACAgIAAxkBAAIBY12345"
    
    AvatarCacheService.set_file_id(test_path, test_file_id)
    cached = AvatarCacheService.get_file_id(test_path)
    assert cached == test_file_id

async def test_chat_service_and_burn_wipe():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        # Create 3 users
        u1 = await UserService.create_user(session, 1001, "alex", "НОЧНОЙ ДЕМОН", "male", "female", 25, "Москва", "bio1", "path1")
        u2 = await UserService.create_user(session, 1002, "anna", "ОПАСНАЯ МАЛЫШКА", "female", "male", 23, "Москва", "bio2", "path2")
        u3 = await UserService.create_user(session, 1003, "elena", "ТАЙНАЯ ЛЕДИ", "female", "male", 24, "Москва", "bio3", "path3")

        # 1. Multi-chat: u1 matches with u2 AND u3
        chat1 = await ChatService.create_or_get_session(session, u1.id, u2.id)
        chat2 = await ChatService.create_or_get_session(session, u1.id, u3.id)
        assert chat1.id != chat2.id

        # Check active chats list for u1
        active_chats = await ChatService.get_user_active_sessions(session, u1.id)
        assert len(active_chats) == 2
        partners = [p.first_name for _, p in active_chats]
        assert "ОПАСНАЯ МАЛЫШКА" in partners
        assert "ТАЙНАЯ ЛЕДИ" in partners

        # 2. Record relayed messages with text and media
        m1 = await ChatService.record_relayed_message(session, chat1.id, u1.id, 501, 601, text="Привет!", media_type="text")
        m2 = await ChatService.record_relayed_message(session, chat1.id, u2.id, 602, 502, text="Привет! Как дела?", media_type="text")
        assert m1.id is not None
        assert m2.id is not None

        recent = await ChatService.get_recent_messages(session, chat1.id)
        assert len(recent) == 2
        assert recent[0].text == "Привет!"
        assert recent[1].text == "Привет! Как дела?"

        # 3. Simulate bot deleting messages upon burning chat1
        mock_bot = AsyncMock()
        mock_bot.delete_message = AsyncMock(return_value=True)

        success, user_a, user_b = await ChatService.burn_and_close_chat(mock_bot, session, chat1.id, u1.id)
        assert success is True
        assert {user_a.id, user_b.id} == {u1.id, u2.id}

        # Verify bot.delete_message was called for all sender and recipient message IDs
        # 501, 601, 602, 502
        assert mock_bot.delete_message.call_count == 4
        deleted_msgs = [(call.kwargs.get("chat_id"), call.kwargs.get("message_id")) for call in mock_bot.delete_message.call_args_list]
        assert (u1.telegram_id, 501) in deleted_msgs
        assert (u2.telegram_id, 601) in deleted_msgs
        assert (u2.telegram_id, 602) in deleted_msgs
        assert (u1.telegram_id, 502) in deleted_msgs

        # Verify chat1 is closed and chat2 is still active
        updated_chat1 = await ChatService.get_session_by_id(session, chat1.id)
        assert updated_chat1.status == "closed"

        active_chats_after = await ChatService.get_user_active_sessions(session, u1.id)
        assert len(active_chats_after) == 1
        assert active_chats_after[0][0].id == chat2.id

    await engine.dispose()

async def test_secret_media():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        u1 = await UserService.create_user(session, 2001, "alex", "НОЧНОЙ ДЕМОН", "male", "female", 25, "Москва", "bio1", "path1")
        u2 = await UserService.create_user(session, 2002, "anna", "ОПАСНАЯ МАЛЫШКА", "female", "male", 23, "Москва", "bio2", "path2")
        chat = await ChatService.create_or_get_session(session, u1.id, u2.id)

        secret = SecretMedia(
            session_id=chat.id,
            sender_id=u1.id,
            recipient_id=u2.id,
            file_id="AgACAgIAAxkBA...",
            caption="Secret snap",
            duration=30,
            is_viewed=False
        )
        session.add(secret)
        await session.commit()
        await session.refresh(secret)

        assert secret.id is not None
        assert secret.duration == 30
        assert secret.is_viewed is False

        # Mark viewed
        secret.is_viewed = True
        await session.commit()

        updated = await session.get(SecretMedia, secret.id)
        assert updated.is_viewed is True

    await engine.dispose()

async def test_couple_personas_and_search_filters():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        from bot.services.persona_service import get_personas_by_gender, get_random_persona
        couples = get_personas_by_gender("couple")
        assert len(couples) == 20
        c_rnd = get_random_persona("couple")
        assert c_rnd.gender == "couple"
        assert c_rnd.name != ""

        u_couple = await UserService.create_user(
            session=session,
            telegram_id=3001,
            username="bonnie_clyde",
            first_name="Бонни и Клайд",
            gender="couple",
            target_gender="female",
            age=26,
            city="Москва",
            bio="Ищем подругу",
            avatar_path="assets/avatars/couple/couple_02.jpg",
            search_city="Москва",
            search_age_min=20,
            search_age_max=30
        )
        assert u_couple.gender == "couple"
        assert u_couple.search_city == "Москва"
        assert u_couple.search_age_min == 20

        u_female_accepts = await UserService.create_user(
            session=session,
            telegram_id=3002,
            username="anna_couple_fan",
            first_name="Анна",
            gender="female",
            target_gender="couple",
            age=24,
            city="Москва",
            bio="Люблю пары",
            avatar_path="path2"
        )

        u_female_males_only = await UserService.create_user(
            session=session,
            telegram_id=3003,
            username="elena_males_only",
            first_name="Елена",
            gender="female",
            target_gender="male",
            age=25,
            city="Москва",
            bio="Только парни",
            avatar_path="path3"
        )

        u_female_spb = await UserService.create_user(
            session=session,
            telegram_id=3004,
            username="olga_spb",
            first_name="Ольга",
            gender="female",
            target_gender="all",
            age=24,
            city="Санкт-Петербург",
            bio="Питер",
            avatar_path="path4"
        )

        u_female_older = await UserService.create_user(
            session=session,
            telegram_id=3005,
            username="tatiana",
            first_name="Татьяна",
            gender="female",
            target_gender="all",
            age=45,
            city="Москва",
            bio="Старше",
            avatar_path="path5"
        )

        matched_pair = await MatchingService.get_next_profile(session, u_couple)
        assert matched_pair is not None
        candidate, _ = matched_pair
        assert candidate.id == u_female_accepts.id

    await engine.dispose()

async def test_delete_user_completely():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        from sqlalchemy import select
        u1 = await UserService.create_user(session, 4001, "del_user", "УДАЛЯЕМЫЙ", "male", "female", 25, "Москва", "bio", "path_del")
        u2 = await UserService.create_user(session, 4002, "other_user", "ДРУГОЙ", "female", "male", 24, "Москва", "bio", "path_other")

        chat = await ChatService.create_or_get_session(session, u1.id, u2.id)
        await ChatService.record_relayed_message(session, chat.id, u1.id, 10, 20, "Привет")
        await MatchingService.record_reaction(session, u1, u2.id, "like")

        mock_bot = AsyncMock()
        success = await UserService.delete_user_completely(mock_bot, session, u1.id)
        assert success is True

        check_u1 = await UserService.get_by_id(session, u1.id)
        assert check_u1 is None

        res_sess = await session.execute(select(ChatSession).where(ChatSession.id == chat.id))
        assert res_sess.scalar_one_or_none() is None

    await engine.dispose()

async def test_couple_profile_and_age():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        u_couple = await UserService.create_user(
            session=session,
            telegram_id=5001,
            username="bonnie_clyde",
            first_name="БОННИ И КЛАЙД",
            gender="couple",
            target_gender="couple",
            age=27,
            city="Москва",
            bio="Ищем вторую пару для общения",
            avatar_path="path_couple",
            couple_age="28/25"
        )
        assert u_couple.couple_age == "28/25"

        cap_owner = UserService.format_caption(u_couple, is_owner=True)
        assert "👥 <b>Анкета пары:</b>" in cap_owner
        assert "28/25" in cap_owner
        assert "🎯 Ищем: <b>пары 👥</b>" in cap_owner

        cap_viewer = UserService.format_caption(u_couple, is_owner=False)
        assert "👥 <b>БОННИ И КЛАЙД</b>, 28/25" in cap_viewer

        updated = await UserService.update_user(session, u_couple.id, couple_age="30/27", age=29)
        assert updated.couple_age == "30/27"
        cap_updated = UserService.format_caption(updated, is_owner=False)
        assert "30/27" in cap_updated

async def test_admin_analytics_and_fake_matching():
    from bot.services.admin_service import AdminService
    from bot.services.seed_service import SeedService

    engine = create_async_engine(TEST_DB_URL, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        # 1. Create a viewer
        viewer = await UserService.create_user(session, 6001, "real_viewer", "ЗРИТЕЛЬ", "male", "female", 25, "Москва", "bio", "path_v")

        # 2. Create 1 fake female and 1 real female in same city & age
        u_fake = await UserService.create_user(session, 6002, "fake_girl", "БОТ ДЕВУШКА", "female", "male", 24, "Москва", "bio", "path_f", is_fake=True)
        u_real = await UserService.create_user(session, 6003, "real_girl", "РЕАЛЬНАЯ ДЕВУШКА", "female", "male", 24, "Москва", "bio", "path_r", is_fake=False)

        # 3. Matching MUST prioritize real user u_real
        pair1 = await MatchingService.get_next_profile(session, viewer)
        assert pair1 is not None
        candidate1, _ = pair1
        assert candidate1.id == u_real.id, f"Expected real user {u_real.id}, got {candidate1.id}"

        # 4. React to u_real, then fake user u_fake should appear
        await MatchingService.record_reaction(session, viewer, u_real.id, "like")
        pair2 = await MatchingService.get_next_profile(session, viewer)
        assert pair2 is not None
        candidate2, _ = pair2
        assert candidate2.id == u_fake.id

        # 5. Test activity tracking
        await AdminService.record_user_activity(session, viewer.id)

        # 6. Test password protection settings and gate
        assert await AdminService.is_password_protection_enabled(session) is False
        await AdminService.set_setting(session, "access_password_enabled", "1")
        await AdminService.set_setting(session, "access_password", "topsecret")
        assert await AdminService.is_password_protection_enabled(session) is True
        assert await AdminService.get_access_password(session) == "topsecret"

        # Gate authorization
        assert await AdminService.is_user_authorized_for_gate(session, 6001) is False
        await AdminService.authorize_user_for_gate(session, 6001)
        assert await AdminService.is_user_authorized_for_gate(session, 6001) is True

        # 7. Test analytics summary
        summary = await AdminService.get_analytics_summary(session)
        assert summary["total_users"] >= 3
        assert summary["real_users"] >= 2
        assert summary["fake_users"] >= 1
        assert summary["pass_enabled"] is True

    await engine.dispose()

async def test_personal_password_and_keyboards():
    from bot.keyboards.inline import (
        get_settings_keyboard,
        get_search_filters_keyboard,
        get_filter_city_keyboard,
        get_filter_age_keyboard,
        get_persona_menu_keyboard,
        get_delete_profile_keyboard,
        get_personal_password_keyboard
    )
    from bot.keyboards.reply import get_main_keyboard

    # 1. Test 2-column layouts
    kb_settings = get_settings_keyboard(is_active=True, is_couple=False, has_password=False)
    for row in kb_settings.inline_keyboard:
        assert len(row) <= 2, f"Row has {len(row)} buttons, expected <= 2: {row}"
    assert len(kb_settings.inline_keyboard) == 7, f"Expected 7 rows, got {len(kb_settings.inline_keyboard)}"

    kb_filters = get_search_filters_keyboard("Москва", 20, 30, "female")
    for row in kb_filters.inline_keyboard:
        assert len(row) <= 2

    kb_city = get_filter_city_keyboard("Москва")
    for row in kb_city.inline_keyboard:
        assert len(row) <= 2

    kb_age = get_filter_age_keyboard()
    for row in kb_age.inline_keyboard:
        assert len(row) <= 2

    kb_persona = get_persona_menu_keyboard()
    for row in kb_persona.inline_keyboard:
        assert len(row) <= 2

    kb_del = get_delete_profile_keyboard()
    assert len(kb_del.inline_keyboard[0]) == 2

    kb_main_lock = get_main_keyboard(has_lock=True)
    assert any(b.text == "🔒 Заблокировать" for row in kb_main_lock.keyboard for b in row)

    # 2. Test personal password set, verify, remove in DB
    engine = create_async_engine(TEST_DB_URL, echo=False)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        u = await UserService.create_user(session, 7001, "pinuser", "ПИН ПОЛЬЗОВАТЕЛЬ", "male", "female", 26, "Москва", "bio", "path")
        assert u.personal_password is None
        assert await UserService.verify_personal_password(session, u.id, "any") is True

        # Set password
        await UserService.set_personal_password(session, u.id, "1234")
        assert await UserService.verify_personal_password(session, u.id, "1234") is True
        assert await UserService.verify_personal_password(session, u.id, "9999") is False

        # Remove password
        await UserService.remove_personal_password(session, u.id)
        u_updated = await UserService.get_by_id(session, u.id)
        assert u_updated.personal_password is None
        assert await UserService.verify_personal_password(session, u.id, "anything") is True

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_avatar_cache_service())
    asyncio.run(test_chat_service_and_burn_wipe())
    asyncio.run(test_secret_media())
    asyncio.run(test_couple_personas_and_search_filters())
    asyncio.run(test_delete_user_completely())
    asyncio.run(test_couple_profile_and_age())
    asyncio.run(test_admin_analytics_and_fake_matching())
    asyncio.run(test_personal_password_and_keyboards())
    print("ALL TESTS PASSED SUCCESSFULLY! [OK]")



