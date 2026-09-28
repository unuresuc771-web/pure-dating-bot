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
    "Свободен сегодня после 21:00. Вино, отель и ночь без лишних слов 🍷",
    "Спортивный, щедрый. Заберу на машине, поужинаем и в номер 😉",
    "Ищу девушку для тайных встреч без выноса мозга. Конфиденциально 🖤",
    "Хочется расслабиться в уютных апартаментах с бокалом просекко ✨",
    "Тактильный, страстный, умею доставить удовольствие. Без обязательств 🔥",
    "Спонтанный вечер в хорошем отеле. Если легкая на подъем — поехали 🚗",
    "Люблю красивое белье и раскованных девушек. Напиши, если за реал 🫦",
    "Уютный номер в центре забронирован. Составишь компанию на вино? 🥂",
    "Без брачных намерений. Чистая страсть, кайф и взаимное уважение 😈",
    "Адекватный парень в форме. Сделаю потрясающий массаж этой ночью 💆‍♂️",
    "Ищу привлекательную спутницу на вечер. Все условия с меня 🖤",
    "Не люблю долгие переписки. Если есть искра — увидимся сегодня 🍷",
    "Горячая ночь в центре города. Напиши, если свободна и хочешь огня 🔥",
    "Щедрый, аккуратный. Заберу тебя в любое время. Готова сорваться? 🚘",
    "Обожаю тактильность, долгие ласки и смелых девушек. Жду твой лайк 🫦",
    "Бокал просекко, красивый вид и только мы вдвоем... Напиши мне ✨",
    "Ищу раскованную подругу для регулярных встреч для удовольствия 😉",
    "Ценю искренность, чистоплотность и страсть. С меня — комфорт 🍾",
    "Спонтанный секс по взаимной симпатии. Без ожиданий и драмы 🔥",
    "Свободен сегодня. Сделаю эту ночь незабываемой для нас обоих 🥂"
]

FEMALE_BIOS = [
    "Хочется живой химии и страсти этой ночью. Свободна с 20:00 😉",
    "Бокал вина в центре, отель и только мы вдвоем... Давай встретимся 🥂",
    "Ищу любовника для регулярных тайных встреч без обязательств 🖤",
    "Тактильная, люблю массаж и уверенные мужские руки. Заберешь меня? 🔥",
    "Планы на ночь? У меня свободно) Хочется тепла и безумства ✨",
    "Не люблю долгие переписки. Если понравились — встретимся сегодня 🚗",
    "Раскрепощенная, фигура 🔥 Ищу щедрого мужчину на вечер",
    "Вкусное вино, красивое белье и горячее продолжение... Напиши мне 🫦",
    "Спонтанная, люблю ночной город и классных парней. Покатаемся? 🚘",
    "Без обязательств и претензий. Только секс по взаимному притяжению 😈",
    "Юрист днем, ночью совсем другая) Хочу расслабиться в компании 🍷",
    "Люблю уверенных мужчин с чувством юмора. С меня — отличный вечер ✨",
    "Студентка. Люблю парней постарше, которые знают толк в удовольствии 🫦",
    "Хочу сорваться этой ночью в отель с классным мужчиной. Вино готово 🍾",
    "Нежная, тактильная, без комплексов. Ищу своего человека для встреч 🖤",
    "Пригласи меня на коктейль, а там посмотрим, насколько совпадем 😉",
    "Хочу забыть про работу и отдаться страсти. Свободна прямо сейчас 🔥",
    "Люблю красивый отдых, массаж с маслами и долгие поцелуи 🫦",
    "Ищу мужчину для красивого романа без лишних вопросов 🥂",
    "Готова к спонтанной встрече через пару часов. Напиши, если смелый 😈"
]

COUPLE_BIOS = [
    "Симпатичная пара. Ищем девушку на бокал вина и страстную ночь 🍷✨",
    "Открытые, без комплексов. Ищем компанию на вечер в апартаменты 🔥",
    "Красивый отдых, отель в центре и море удовольствия без табу 🥂",
    "Пара М+Ж. Ищем третью для ярких эмоций и полного релакса 🖤",
    "Молодые, горячие. Ждем раскрепощенную спутницу на эту ночь 🍾",
    "Ищем вторую пару или девушку для общения и горячего продолжения 🫦",
    "Эстетичные, успешные. Любим хорошее вино и эксперименты в постели ✨",
    "Пара со стажем, хотим добавить огня. Чистота и безопасность на 100% 🖤",
    "С нас вино, уютная атмосфера и забота. С тебя — легкий вайб 🥂",
    "Ищем раскованную девушку для совместных ласк без обязательств 🔥",
    "Любим путешествия, вечеринки и качественный секс без драмы 🍷",
    "Открытый формат общения. Давайте знакомиться и выпьем в баре 🍸",
    "Ищем компанию на ночь в апартаменты. Просекко уже охлаждается 🍾",
    "Пара со свободными взглядами. Ищем подругу для ярких встреч ✨",
    "Тактильные, нежные, любим массаж втроем и долгие ночи 🫦",
    "Без пошлости, со вкусом. Ищем третью для незабываемой ночи 🥂",
    "Молодая пара, ищем раскованную девушку для совместного кайфа 🔥",
    "Апартаменты в центре, лаунж и полная свобода желаний 🖤",
    "Ищем интересную спутницу для регулярных встреч. Конфиденциально 🍷",
    "Готовы к спонтанному вечеру прямо сейчас. Напишите нам 😉"
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
