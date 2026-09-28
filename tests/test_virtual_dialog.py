import asyncio
import os
import random
import unittest
from sqlalchemy import select
from bot.database.db import async_session_maker, init_db
from bot.database.models import User, ChatSession, ChatMessage, Reaction, Match, utc_now
from bot.services.user_service import UserService
from bot.services.admin_service import AdminService
from bot.services.matching import MatchingService
from bot.services.chat_service import ChatService
from bot.services.virtual_chat_engine import VirtualChatEngine, ARCHETYPES, REPLIES

class TestVirtualDialog(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await init_db()

    async def test_archetypes_and_replies_coverage(self):
        """Проверяем, что для всех полов и стадий (1-10) есть разнообразные реплики."""
        for gender, archetypes in ARCHETYPES.items():
            for arch in archetypes:
                self.assertIn(arch, REPLIES, f"Archetype {arch} must be in REPLIES")
                arch_dict = REPLIES[arch]
                for stage in range(1, 11):
                    self.assertIn(stage, arch_dict, f"Stage {stage} missing in {arch}")
                    options = arch_dict[stage]
                    self.assertTrue(len(options) >= 3, f"Stage {stage} in {arch} must have at least 3 variations")
                    for opt in options:
                        self.assertIsInstance(opt, str)
                        self.assertTrue(len(opt) > 5)

    async def test_generate_reply_and_slot_filling(self):
        """Проверяем подстановку города и разнообразие текстов."""
        user = User(id=1, first_name="Алексей", city="Москва", gender="male")
        fake_user = User(id=2, first_name="Анна", city="Москва", gender="female", is_fake=True)

        # Стадия 2 часто использует {city}
        replies = set()
        for _ in range(10):
            r = VirtualChatEngine.generate_reply(stage=2, archetype="coquette", user=user, fake_user=fake_user)
            self.assertNotIn("{city}", r, "Slot {city} must be replaced!")
            replies.add(r)
        
        # Разнообразие: получено больше 1 уникального ответа
        self.assertTrue(len(replies) > 1, "Replies should be varied and non-templated")

    async def test_match_back_rate_setting(self):
        """Проверяем чтение и изменение шанса отклика в AdminService."""
        async with async_session_maker() as session:
            await AdminService.set_virtual_match_rate(session, 0.15)
            rate = await AdminService.get_virtual_match_rate(session)
            self.assertAlmostEqual(rate, 0.15)

            await AdminService.set_virtual_match_rate(session, 0.50)
            rate2 = await AdminService.get_virtual_match_rate(session)
            self.assertAlmostEqual(rate2, 0.50)

            # Возвращаем 0.15
            await AdminService.set_virtual_match_rate(session, 0.15)

    async def test_virtual_match_simulation(self):
        """Проверяем, что при rate=1.0 лайк реального человека всегда создает взаимный мэтч с виртуалом."""
        async with async_session_maker() as session:
            # Создаем тестового реального пользователя с уникальным telegram_id
            rand_id = random.randint(100000000, 999999999)
            real_u = User(
                telegram_id=rand_id,
                first_name="ТестРеал",
                gender="male",
                age=25,
                city="Москва",
                avatar_path="test.jpg",
                is_fake=False
            )
            fake_u = User(
                telegram_id=-rand_id,
                first_name="ТестВиртуал",
                gender="female",
                age=23,
                city="Москва",
                avatar_path="test.jpg",
                is_fake=True
            )
            session.add_all([real_u, fake_u])
            await session.commit()
            await session.refresh(real_u)
            await session.refresh(fake_u)

            # Устанавливаем rate = 1.0 (100% отклик для теста)
            await AdminService.set_virtual_match_rate(session, 1.0)

            is_match, target = await MatchingService.record_reaction(
                session=session,
                from_user=real_u,
                target_user_id=fake_u.id,
                reaction_type="like"
            )
            self.assertTrue(is_match, "Should be mutual match with 100% rate")
            self.assertEqual(target.id, fake_u.id)

            # Возвращаем rate = 0.15
            await AdminService.set_virtual_match_rate(session, 0.15)

    async def test_full_10_stage_dialog_progression(self):
        """Проверяем генерацию 10 стадий диалога: от знакомства к предложению встречи и сжиганию."""
        user = User(id=10, first_name="Иван", city="Санкт-Петербург", gender="male")
        fake_user = User(id=11, first_name="Дарья", city="Санкт-Петербург", gender="female", is_fake=True)

        arch = VirtualChatEngine.get_archetype_for_user(fake_user)
        self.assertIn(arch, ARCHETYPES["female"])

        dialog_history = []
        for stage in range(1, 11):
            msg = VirtualChatEngine.generate_reply(stage=stage, archetype=arch, user=user, fake_user=fake_user)
            dialog_history.append((stage, msg))
            self.assertTrue(len(msg) > 0)

        # Стадия 9 должна содержать предложение встречи / призыв к действию
        stage_9_msg = dialog_history[8][1].lower()
        self.assertTrue(
            any(w in stage_9_msg for w in ["встрет", "увид", "погнали", "пересеч", "кофе", "вина", "сегодня", "ночью"]),
            f"Stage 9 should propose a meeting: {stage_9_msg}"
        )

        # Стадия 10 должна содержать намек на сгорание / правила Pure
        stage_10_msg = dialog_history[9][1].lower()
        self.assertTrue(
            any(w in stage_10_msg for w in ["сгор", "сгорит", "исчез", "время", "pure", "таймер", "стерт", "бабах"]),
            f"Stage 10 should announce chat burning: {stage_10_msg}"
        )

    async def test_delayed_virtual_match(self):
        """Проверяем отложенное создание взаимного мэтча и сессии диалога."""
        async with async_session_maker() as session:
            rand_id2 = random.randint(100000000, 999999999)
            real_u = User(
                telegram_id=rand_id2,
                first_name="ТестРеал2",
                gender="male",
                age=27,
                city="Москва",
                avatar_path="test.jpg",
                is_fake=False
            )
            fake_u = User(
                telegram_id=-rand_id2,
                first_name="ТестВиртуал2",
                gender="female",
                age=24,
                city="Москва",
                avatar_path="test.jpg",
                is_fake=True
            )
            session.add_all([real_u, fake_u])
            await session.commit()
            await session.refresh(real_u)
            await session.refresh(fake_u)

            from unittest.mock import AsyncMock
            mock_bot = AsyncMock()

            # Вызываем с задержкой 0 секунд
            await VirtualChatEngine._execute_delayed_match(
                bot=mock_bot,
                real_user_id=real_u.id,
                fake_user_id=fake_u.id,
                min_delay=0,
                max_delay=0
            )

            # Проверяем, что в БД появились Reaction, Match и ChatSession
            u1, u2 = min(real_u.id, fake_u.id), max(real_u.id, fake_u.id)
            match_res = await session.execute(select(Match).where(Match.user1_id == u1, Match.user2_id == u2))
            self.assertIsNotNone(match_res.scalar_one_or_none(), "Match must be created!")

            chat_res = await session.execute(select(ChatSession).where(ChatSession.user_a_id == u1, ChatSession.user_b_id == u2))
            self.assertIsNotNone(chat_res.scalar_one_or_none(), "ChatSession must be created!")

if __name__ == "__main__":
    unittest.main()
