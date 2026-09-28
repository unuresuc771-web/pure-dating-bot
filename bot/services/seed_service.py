import random
import os
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, utc_now
from bot.services.persona_service import get_personas_by_gender

CITIES = [
    "Москва", "Санкт-Петербург", "Казань", "Новосибирск", "Екатеринбург",
    "Нижний Новгород", "Краснодар", "Сочи", "Минск", "Ростов-на-Дону",
    "Самара", "Уфа", "Тюмень", "Воронеж", "Пермь", "Калининград",
    "Владивосток", "Иркутск", "Ярославль", "Алматы"
]

MALE_NAMES = [
    "Александр", "Максим", "Артём", "Дмитрий", "Никита", "Роман", "Илья", "Даниил",
    "Владислав", "Кирилл", "Егор", "Ярослав", "Денис", "Михаил", "Сергей", "Марк",
    "Павел", "Тимофей", "Глеб", "Арсений", "Матвей", "Антон", "Виктор", "Георгий"
]

FEMALE_NAMES = [
    "Анна", "Дарья", "Алина", "Полина", "Виктория", "София", "Ксения", "Валерия",
    "Диана", "Мила", "Яна", "Кристина", "Вероника", "Алиса", "Елена", "Мария",
    "Карина", "Анастасия", "Юлия", "Елизавета", "Маргарита", "Светлана", "Инна", "Элина"
]

COUPLE_NAMES = [
    "Опасный Дуэт", "Бонни и Клайд", "Дикая Любовь", "Ночные Хищники", "Сладкий Грех",
    "Тайный Союз", "Электрическая Пара", "Грешный Рай", "Двойной Соблазн", "Теневой Альянс",
    "В ритме Танго", "Пылкий Джаз", "Неоновые Беглецы", "Алая Страсть", "Темные Любовники",
    "Сумасшедший Тандем", "Игры с Огнем", "Кибер Влюбленные", "Запретный Плод", "Полночный Экспресс",
    "Пара М&Ж", "Alex & Eva", "Max & Kate", "Ночные Птицы", "Пара из центра", "Адам и Ева",
    "Безумная Любовь", "Латина Пара", "Два Сердца", "Элита Дуэт"
]

MALE_BIOS = [
    "Люблю вечерний город, хороший кофе и спонтанные поездки 🚗",
    "Ищу приятное и лёгкое общение без лишних драм и сложностей.",
    "Работаю в IT, в свободное время зал, музыка и прогулки.",
    "Хочется тепла, искренности и интересного собеседника.",
    "Здесь ради хорошей компании, классного вайба и новых впечатлений.",
    "Архитектор. Ценю чувство юмора, стиль и острый ум.",
    "Давай выпьем кофе и поговорим обо всём на свете ☕️",
    "Слушаю винил, люблю готовить вкусную пасту и гулять ночами.",
    "Предприниматель. Ценю искренность, открытость и живой интерес.",
    "Обожаю горы, сноуборд и душевные вечерние разговоры.",
    "Спокойный, с чувством юмора. Ищу свою музу ✨",
    "Люблю джаз, театр и открытых людей с огоньком в глазах.",
    "Просто парень, который ищет приятное знакомство.",
    "Ценю уют, честность и лёгкость в общении.",
    "Занимаюсь спортом, люблю кино и долгие прогулки по набережной."
]

FEMALE_BIOS = [
    "Дизайнер интерьеров, обожаю выставки и уютные кофейни 🌿",
    "Ценю лёгкость в общении, интеллект и тонкое чувство юмора.",
    "Если умеешь поддержать классный диалог — мы точно поладим 😉",
    "Спонтанные поездки, море и душевные разговоры до утра ✨",
    "Люблю кино, книги, эстетику и атмосферные места.",
    "Хочется приятного вайба, искры и тёплого общения.",
    "Фотографирую, много путешествую и верю в судьбоносные встречи 📸",
    "Творю, вдохновляюсь искусством, варю самый вкусный кофе.",
    "Психолог и гедонист. Люблю людей со вкусом к жизни.",
    "Ищу человека на одной волне для искреннего общения.",
    "Люблю танцы, пионы и искренние комплименты 🌸",
    "Иногда спонтанная, иногда домашняя. Буду рада знакомству!",
    "Эстетика во всём. Ценю мужские поступки и заботу.",
    "Люблю путешествия, современное искусство и тёплые объятия."
]

COUPLE_BIOS = [
    "Красивая пара. Ищем вторую пару или симпатичную девушку для общения и совместных вечеров 🍷",
    "Открытые и позитивные. Любим путешествия, вкусное вино и интересные беседы.",
    "Свободные взгляды, ценим эстетику и классный вайб. Без предрассудков и лишних рамок ✨",
    "Молодая и стильная пара. Ищем компанию для посиделок в барах и тусовок.",
    "Ищем людей на одной волне для ярких эмоций и классного досуга.",
    "Любим настолки, вечеринки, караоке и ночной город. Будем рады новым знакомствам 👥",
    "Гармоничная пара. Открыты к новым интересным людям и необычным форматам общения.",
    "Позитивные, лёгкие на подъём. Ищем приятных собеседников и компанию для отдыха.",
    "Любим вкусную еду, кино и откровенные душевные разговоры.",
    "Вместе создаём классные воспоминания. Давайте знакомиться!"
]

class SeedService:
    @staticmethod
    async def seed_fake_users(session: AsyncSession, count_per_type: int = 100) -> dict:
        """
        Создает виртуальных пользователей: count_per_type мужчин, женщин и пар.
        """
        male_personas = get_personas_by_gender("male")
        female_personas = get_personas_by_gender("female")
        couple_personas = get_personas_by_gender("couple")

        base_tg_id = 900000000
        now = utc_now()

        created_counts = {"male": 0, "female": 0, "couple": 0}

        # 1. 100 Мужчин
        for i in range(count_per_type):
            tg_id = base_tg_id + 10000 + i
            # Проверяем, существует ли уже
            exists = (await session.execute(select(User.id).where(User.telegram_id == tg_id))).scalar_one_or_none()
            if exists:
                continue

            persona = male_personas[i % len(male_personas)]
            name = random.choice(MALE_NAMES) if i % 2 == 0 else persona.name
            age = random.randint(20, 42)
            city = random.choice(CITIES)
            bio = random.choice(MALE_BIOS)
            target = random.choices(["female", "couple", "all"], weights=[80, 10, 10])[0]
            created_at = now - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))

            u = User(
                telegram_id=tg_id,
                username=None,
                first_name=name,
                gender="male",
                target_gender=target,
                age=age,
                city=city,
                bio=bio,
                avatar_path=persona.avatar_path,
                is_custom_photo=False,
                is_active=True,
                is_banned=False,
                is_fake=True,
                created_at=created_at,
                last_seen_at=now - timedelta(hours=random.randint(1, 48))
            )
            session.add(u)
            created_counts["male"] += 1

        # 2. 100 Женщин
        for i in range(count_per_type):
            tg_id = base_tg_id + 20000 + i
            exists = (await session.execute(select(User.id).where(User.telegram_id == tg_id))).scalar_one_or_none()
            if exists:
                continue

            persona = female_personas[i % len(female_personas)]
            name = random.choice(FEMALE_NAMES) if i % 2 == 0 else persona.name
            age = random.randint(18, 38)
            city = random.choice(CITIES)
            bio = random.choice(FEMALE_BIOS)
            target = random.choices(["male", "couple", "all"], weights=[80, 10, 10])[0]
            created_at = now - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))

            u = User(
                telegram_id=tg_id,
                username=None,
                first_name=name,
                gender="female",
                target_gender=target,
                age=age,
                city=city,
                bio=bio,
                avatar_path=persona.avatar_path,
                is_custom_photo=False,
                is_active=True,
                is_banned=False,
                is_fake=True,
                created_at=created_at,
                last_seen_at=now - timedelta(hours=random.randint(1, 48))
            )
            session.add(u)
            created_counts["female"] += 1

        # 3. 100 Пар
        for i in range(count_per_type):
            tg_id = base_tg_id + 30000 + i
            exists = (await session.execute(select(User.id).where(User.telegram_id == tg_id))).scalar_one_or_none()
            if exists:
                continue

            persona = couple_personas[i % len(couple_personas)]
            name = random.choice(COUPLE_NAMES) if i % 2 == 0 else persona.name
            a1 = random.randint(22, 38)
            a2 = a1 + random.randint(-4, 3)
            a2 = max(18, a2)
            couple_age = f"{a1}/{a2}"
            avg_age = round((a1 + a2) / 2)
            city = random.choice(CITIES)
            bio = random.choice(COUPLE_BIOS)
            target = random.choices(["couple", "female", "all", "male"], weights=[50, 25, 20, 5])[0]
            created_at = now - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))

            u = User(
                telegram_id=tg_id,
                username=None,
                first_name=name,
                gender="couple",
                target_gender=target,
                age=avg_age,
                couple_age=couple_age,
                city=city,
                bio=bio,
                avatar_path=persona.avatar_path,
                is_custom_photo=False,
                is_active=True,
                is_banned=False,
                is_fake=True,
                created_at=created_at,
                last_seen_at=now - timedelta(hours=random.randint(1, 48))
            )
            session.add(u)
            created_counts["couple"] += 1

        await session.commit()
        return created_counts

    @staticmethod
    async def clear_fake_users(session: AsyncSession) -> int:
        stmt = delete(User).where(User.is_fake.is_(True))
        res = await session.execute(stmt)
        await session.commit()
        return res.rowcount
