import random
import os
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, Reaction, Match, utc_now

CITIES = [
    "Москва", "Санкт-Петербург", "Казань", "Новосибирск", "Екатеринбург",
    "Нижний Новгород", "Краснодар", "Сочи", "Минск", "Ростов-на-Дону",
    "Самара", "Уфа", "Тюмень", "Воронеж", "Пермь", "Калининград",
    "Владивосток", "Иркутск", "Ярославль", "Алматы"
]

MALE_NAMES = [
    "Ночной Демон",          # 01
    "Грешный Ангел",         # 02
    "Безумный Кролик",       # 03
    "Чертовски Хорош",       # 04
    "Кибер Дьявол",          # 05
    "Сладкий Яд",            # 06
    "Космический Монстр",    # 07
    "Лукавый Лис",           # 08
    "Дикий Зверь",           # 09
    "Огненный Бунтарь",      # 10
    "Тайный Искуситель",     # 11
    "Бархатный Чёрт",        # 12
    "Мрачный Романтик",      # 13
    "Пьяный Сатир",          # 14
    "Дерзкий Фавн",          # 15
    "Ночной Охотник",        # 16
    "Мистический Бес",       # 17
    "Грешник без вины",      # 18
    "Теневой Идол",          # 19
    "Электрический Демон",   # 20
]

FEMALE_NAMES = [
    "Маленькая Чертовка",    # 01
    "Дикая Кошка",           # 02
    "Сладкая Ведьма",        # 03
    "Грешная Нимфа",         # 04
    "Ночная Бестия",         # 05
    "Кибер Суккуб",          # 06
    "Опасная Малышка",       # 07
    "Ядовитая Мята",         # 08
    "Мятежная Душа",         # 09
    "Лунная Сирена",         # 10
    "Бархатная Пантера",     # 11
    "Искренняя Дьяволица",   # 12
    "Розовая Фурия",         # 13
    "Пылающая Медуза",       # 14
    "Космическая Киска",     # 15
    "Чертовски Милая",       # 16
    "Запретный Плод",        # 17
    "Тайная Грешница",       # 18
    "Дерзкая Искусительница",# 19
    "Огненная Бестия",       # 20
]

COUPLE_NAMES = [
    "Опасный Дуэт",          # 01
    "Бонни и Клайд",         # 02
    "Дикая Любовь",          # 03
    "Ночные Хищники",        # 04
    "Сладкий Грех",          # 05
    "Тайный Союз",           # 06
    "Электрическая Пара",    # 07
    "Грешный Рай",           # 08
    "Двойной Соблазн",       # 09
    "Теневой Альянс",        # 10
    "В ритме Танго",         # 11
    "Пылкий Джаз",           # 12
    "Неоновые Беглецы",      # 13
    "Алая Страсть",          # 14
    "Темные Любовники",      # 15
    "Сумасшедший Тандем",    # 16
    "Игры с Огнем",          # 17
    "Кибер Влюбленные",      # 18
    "Запретный Плод",        # 19
    "Полночный Экспресс",    # 20
]

MALE_BIOS = [
    "Свободен сегодня. Вино, кино или прогуляться, а там как пойдет.",
    "Просто встретиться вечером, пообщаться и отдохнуть. Без обязательств.",
    "В городе проездом. Ищу приятную компанию на вечер.",
    "За приятный вечер тет-а-тет. Ценю комфорт и взаимное притяжение.",
    "Легкий на подъем. Поужинать, выпить и приятно провести время.",
    "Ищу девушку для встреч без драмы и выноса мозга.",
    "Свободный вечер. Если тоже не спится — давай пересечемся.",
    "За спонтанность. Без долгих переписок, лучше сразу вживую.",
    "Спокойный, адекватный. Интересуют встречи для удовольствия.",
    "Свободен после работы. Заеду, выпьем кофе или чего покрепче.",
    "Хочу приятно провести время в хорошей компании. Конфиденциально.",
    "За живое общение и взаимную симпатию. Без сложных заморочек.",
    "Посидеть в приятном месте, поболтать и отдохнуть.",
    "Простые встречи без ожиданий и претензий. Для взаимного релакса.",
    "Люблю спонтанные встречи. Если на одной волне — пиши.",
    "Не люблю долгие переписки ни о чем. За встречу сегодня.",
    "Ищу симпатичную подругу для приятных вечеров.",
    "Вечер свободен. Можно выпить вина и отлично провести время.",
    "Адекватный, чистоплотный. Интересует секс без обязательств.",
    "Без лишних слов. Понравились друг другу — встретились."
]

FEMALE_BIOS = [
    "Свободна сегодня вечером. Хочу просто расслабиться и приятно поболтать.",
    "Не люблю долгие переписки. Если есть симпатия — лучше увидеться.",
    "Ищу приятного мужчину для встреч без обязательств и драмы.",
    "Хочется тепла, бокал вина и хорошую компанию на вечер.",
    "Спонтанная. Если понравимся друг другу — буду рада встрече сегодня.",
    "Просто секс по взаимной симпатии, без выноса мозга и претензий.",
    "Свободный вечер. Буду рада выпить вина в уютном месте.",
    "Ценю чистоплотность, адекватность и легкость в общении.",
    "Хочется отвлечься от рутины и провести вечер в приятной компании.",
    "Ищу любовника для регулярных встреч для взаимного удовольствия.",
    "Без драмы и намеков на серьезное. Просто легкое общение и релакс.",
    "Сегодня одна, дома скучно. Готова выбраться куда-нибудь.",
    "Люблю массаж, вино и долгие разговоры наедине.",
    "Хочу встретить человека, с которым просто приятно и тепло.",
    "Конфиденциально, легко и без лишних вопросов.",
    "За спонтанные встречи, если совпал вайб.",
    "Устала от работы, хочется просто расслабиться этой ночью.",
    "Симпатичная, открытая к приятным знакомствам без обязательств.",
    "Если есть химия — не вижу смысла затягивать переписку.",
    "Ищу надежного и приятного партнера для встреч."
]

COUPLE_BIOS = [
    "Пара. Ищем девушку для приятного вечера за бокалом вина.",
    "Открытые и без комплексов. Ищем компанию на вечер в апартаменты.",
    "Ищем легкую на подъем девушку для новых ярких впечатлений.",
    "М+Ж. Без ревности и драмы, ценим комфорт и взаимное притяжение.",
    "Хотим познакомиться с симпатичной девушкой для совместного отдыха.",
    "Ищем компанию на ночь. Конфиденциальность и безопасность гарантируем.",
    "С нас приятная атмосфера, вино и уют. С тебя — позитивный вайб.",
    "Интересует общение и продолжение без обязательств.",
    "Пара со свободными взглядами. Ищем третью для красивого вечера.",
    "Любим расслабленный отдых, массаж и приятные эксперименты.",
    "Ищем девушку на вечер. Без табу, по взаимному согласию.",
    "Хотим приятно провести время втроем. Давайте знакомиться.",
    "Пара, ищем раскованную подругу для совместных встреч.",
    "Просто хотим отдохнуть в хорошей компании тет-а-тет.",
    "Ценим чистоплотность, открытость и искренность.",
    "Ищем приятную спутницу на эту ночь. Вино уже открыто.",
    "Свободный формат без лишних сложностей.",
    "Интересны встречи втроем по взаимной химии.",
    "Молодая пара. Ищем девушку для душевного и горячего релакса.",
    "Без предрассудков. Встретимся, пообщаемся, а дальше решим."
]

class SeedService:
    @staticmethod
    async def seed_fake_users(session: AsyncSession, count_per_type: int = 100) -> dict:
        """
        Создает или обновляет виртуальных пользователей: count_per_type мужчин, женщин и пар.
        Все имена - 100% соответствуют названиям уникальных 20 аватаров для каждого пола.
        Все описания - реалистичные, откровенные и короткие (в стиле Pure).
        Все пути к фото - кроссплатформенные относительные пути assets/avatars/...
        """
        base_tg_id = 900000000
        now = utc_now()

        created_counts = {"male": 0, "female": 0, "couple": 0}

        # 1. Мужчины (100)
        for i in range(count_per_type):
            tg_id = base_tg_id + 10000 + i
            avatar_idx = i % len(MALE_NAMES)
            avatar_num = avatar_idx + 1
            avatar_rel_path = f"assets/avatars/male/male_{avatar_num:02d}.jpg"
            name = MALE_NAMES[avatar_idx]
            age = random.randint(21, 42)
            city = random.choice(CITIES)
            bio = MALE_BIOS[i % len(MALE_BIOS)]
            target = random.choices(["female", "couple", "all"], weights=[80, 10, 10])[0]
            created_at = now - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))

            existing_user = (await session.execute(select(User).where(User.telegram_id == tg_id))).scalar_one_or_none()
            if existing_user:
                existing_user.first_name = name
                existing_user.gender = "male"
                existing_user.target_gender = target
                existing_user.age = age
                existing_user.city = city
                existing_user.bio = bio
                existing_user.avatar_path = avatar_rel_path
                existing_user.is_custom_photo = False
                existing_user.is_active = True
                existing_user.is_banned = False
                existing_user.is_fake = True
                created_counts["male"] += 1
                continue

            u = User(
                telegram_id=tg_id,
                username=None,
                first_name=name,
                gender="male",
                target_gender=target,
                age=age,
                city=city,
                bio=bio,
                avatar_path=avatar_rel_path,
                is_custom_photo=False,
                is_active=True,
                is_banned=False,
                is_fake=True,
                created_at=created_at,
                last_seen_at=now - timedelta(hours=random.randint(1, 48))
            )
            session.add(u)
            created_counts["male"] += 1

        # 2. Женщины (100)
        for i in range(count_per_type):
            tg_id = base_tg_id + 20000 + i
            avatar_num = (i % 20) + 1
            avatar_rel_path = f"assets/avatars/female/female_{avatar_num:02d}.jpg"
            name = FEMALE_NAMES[i % len(FEMALE_NAMES)]
            age = random.randint(19, 36)
            city = random.choice(CITIES)
            bio = FEMALE_BIOS[i % len(FEMALE_BIOS)]
            target = random.choices(["male", "couple", "all"], weights=[80, 10, 10])[0]
            created_at = now - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))

            existing_user = (await session.execute(select(User).where(User.telegram_id == tg_id))).scalar_one_or_none()
            if existing_user:
                existing_user.first_name = name
                existing_user.gender = "female"
                existing_user.target_gender = target
                existing_user.age = age
                existing_user.city = city
                existing_user.bio = bio
                existing_user.avatar_path = avatar_rel_path
                existing_user.is_custom_photo = False
                existing_user.is_active = True
                existing_user.is_banned = False
                existing_user.is_fake = True
                created_counts["female"] += 1
                continue

            u = User(
                telegram_id=tg_id,
                username=None,
                first_name=name,
                gender="female",
                target_gender=target,
                age=age,
                city=city,
                bio=bio,
                avatar_path=avatar_rel_path,
                is_custom_photo=False,
                is_active=True,
                is_banned=False,
                is_fake=True,
                created_at=created_at,
                last_seen_at=now - timedelta(hours=random.randint(1, 48))
            )
            session.add(u)
            created_counts["female"] += 1

        # 3. Пары (100)
        for i in range(count_per_type):
            tg_id = base_tg_id + 30000 + i
            avatar_num = (i % 20) + 1
            avatar_rel_path = f"assets/avatars/couple/couple_{avatar_num:02d}.jpg"
            name = COUPLE_NAMES[i % len(COUPLE_NAMES)]
            a1 = random.randint(23, 36)
            a2 = a1 + random.randint(-4, 2)
            a2 = max(19, a2)
            couple_age = f"{a1}/{a2}"
            avg_age = round((a1 + a2) / 2)
            city = random.choice(CITIES)
            bio = COUPLE_BIOS[i % len(COUPLE_BIOS)]
            target = random.choices(["couple", "female", "all", "male"], weights=[50, 25, 20, 5])[0]
            created_at = now - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))

            existing_user = (await session.execute(select(User).where(User.telegram_id == tg_id))).scalar_one_or_none()
            if existing_user:
                existing_user.first_name = name
                existing_user.gender = "couple"
                existing_user.target_gender = target
                existing_user.couple_age = couple_age
                existing_user.age = avg_age
                existing_user.city = city
                existing_user.bio = bio
                existing_user.avatar_path = avatar_rel_path
                existing_user.is_custom_photo = False
                existing_user.is_active = True
                existing_user.is_banned = False
                existing_user.is_fake = True
                created_counts["couple"] += 1
                continue

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
                avatar_path=avatar_rel_path,
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
