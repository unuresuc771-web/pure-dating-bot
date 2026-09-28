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
    "Уверенный, щедрый и без заморочек. Ценю красивых раскованных девушек, страсть и ночной город на скорости 🔥",
    "Знаю, как доставить удовольствие и заставить дрожать от прикосновений. Спонтанный номер в отеле, вино и только мы двое 🍷",
    "Никаких нудных переписок. Если есть взаимная искра — заберу тебя этой ночью и подарю незабываемые эмоции 😈",
    "Тактильный, страстный, умею слушать женское тело. Ищу любовницу для ярких регулярных встреч без обязательств 🖤",
    "Люблю сильные эмоции, красивое кружево и когда девушка не стесняется своих желаний. Всё конфиденциально и со вкусом 🫦",
    "Спортивное тело, твердый характер и нежные руки. Готов стать твоим лучшим секретом 😉",
    "Атмосфера, хорошее шампанское, качественный секс и легкое общение. Без драм и взаимных претензий 🥂",
    "Знаю толк в чувственных удовольствиях. Если хочешь расслабиться и отдаться желаниям — ты по адресу 🔥",
    "Ищу девушку для тайных встреч, которая ценит страсть, уверенность и полное раскрепощение 😈",
    "Привык брать инициативу на себя. С меня — уютные апартаменты, напитки и забота, с тебя — твоя раскрепощенность 🫦",
    "Секс по взаимному притяжению, без лишних слов. Почувствуй разницу, когда мужчина знает, что делает 🖤",
    "Люблю эксперименты, искреннее влечение и когда ночь длится до обеда. Напиши, если готова к жаре 😉",
    "Внимательный любовник, щедрый на эмоции. Ценю взаимный комфорт, чистоту и страсть без рамок 🔥",
    "Обожаю долгие прелюдии, массаж с маслами и горячее продолжение. Давай сделаем эту ночь особенной 🍷",
    "Умею удивлять и исполнять женские фантазии. Заглянул в Pure за ярким знакомством без лишних вопросов 😈",
    "Приеду, заберу, подарю незабываемую ночь и отвезу обратно с улыбкой на лице. Ты в деле? 🚗💨",
    "Эстет. Люблю женскую сексуальность, ухоженность и смелость. Если между нами искра — не теряем время 🖤",
    "Харизматичный, надежный, ценю конфиденциальность. Ищу свою музу для страстных ночей 🫦",
    "Никаких драм, только искренняя химия и взаимный кайф. Напиши мне, если ты за спонтанность 🔥",
    "Знаю, чего хочу, и умею давать девушке почувствовать себя желанной на 100%. Жду твой лайк 😉"
]

FEMALE_BIOS = [
    "Ищу мужчину для жарких ночей без драмы и обязательств. Люблю красивое белье, тактильность и когда знают, как доставить удовольствие 🍷🔥",
    "Красивая, раскованная, без комплексов. Хочу страсти, мурашек по телу и чтобы сносило крышу от прикосновений. Ты смелый? 🫦",
    "Не люблю долгие переписки. Бокал сухого, искра между нами и спонтанное продолжение этой ночью у тебя или в отеле... Напиши мне 💋",
    "Здесь ради тайных удовольствий и запретных фантазий. Готова к безумствам с правильным мужчиной. Всё строго конфиденциально 🖤",
    "Тактильная гедонистка. Обожаю массаж с маслами, шелк, поцелуи в шею и когда искры летят во все стороны. Удиви меня 😈",
    "Спортивная фигура, горячий темперамент и ноль занудства. Ищу любовника со вкусом к жизни для регулярных ярких встреч 🔥",
    "Давай без банальностей. Закажи такси, купи хорошее вино, а дальше доверимся инстинктам... Жду твой лайк 🫦",
    "Хочу почувствовать сильные руки на талии и забыть обо всех приличиях. Если ты здесь за тем же — не стесняйся 💋",
    "Спонтанный секс, чистая химия и никакого осадка наутро. Смелые желания только приветствуются 🖤🔥",
    "Позволяю себе быть настоящей. Ищу мужчину, с которым можно сойти с ума в ночном номере отеля до самого утра 🥂",
    "Люблю легкое доминирование, страстные поцелуи и когда от взгляда перехватывает дыхание. Покажи, на что способен 😈",
    "Девушка с огоньком. Люблю плохих парней с хорошими манерами. Заглянула за искренним влечением и горячими ночами 🫦",
    "Никаких ожиданий, только взаимное влечение, кайф и сладкое послевкусие. Готова к встрече сегодня ночью 💋",
    "Открыта к экспериментам, ласке и безудержной ночи. Давай бросим чаты и перейдем к делу 🔥",
    "Обожаю, когда мужчина берет инициативу в свои руки. С тебя — уверенность и атмосфера, с меня — моя страсть и нежность 🖤",
    "Эстетика обнаженного тела, вкусный парфюм и долгие ласки. Ищу того, кто умеет заводить с полуслова 🫦",
    "Не ищу мужа. Ищу огонь, страсть и искру, от которой плавятся простыни. Если готов — отвечай взаимностью 😉🔥",
    "Люблю спонтанность. Если совпадем вайбом — встретимся уже через пару часов 🍸",
    "Сладкая, дерзкая и открытая к ярким эмоциям. Жду того, кто не боится своих желаний 💋",
    "Чистая страсть в стиле Pure. Заходи, если хочешь забыть обо всем и отдаться моменту 😈🔥"
]

COUPLE_BIOS = [
    "Красивая раскованная пара (М+Ж). Ищем симпатичную раскованную девушку для чувственного треугольника и яркой ночи без табу 🥂✨",
    "Эстетичные и раскрепощенные. Ищем третью или вторую пару для воплощения тайных фантазий в уютной атмосфере отеля 🍷🔥",
    "Любим качественный секс, массаж, вино и полное доверие. Без комплексов и ханжества. Приглашаем к нам на бокал 😈",
    "Пара со стажем, но с неугасающей страстью. Ищем яркую девушку для совместных ласк и незабываемых впечатлений 🖤",
    "Готовы к смелым экспериментам. Внимательные, нежные и горячие любовники. Полная конфиденциальность гарантирована 🫦",
    "Красивые тела, свободные взгляды. Ищем компаньона(ку) для горячих вечеров, шампанского и чувственного релакса 🍾",
    "Любим ролевые игры, тактильность и когда нет никаких запретов. Напиши нам — ночь будет жаркой! 🔥",
    "Молодые, страстные, без комплексов. Ищем третьего(тью) для горячего продолжения в лаунже или апартаментах ✨",
    "Ищем людей на одной волне для ярких интимных эмоций и эстетичного секса без предрассудков 🍷",
    "Чувственные, открытые, тактильные. Подарим незабываемую ночь взаимного удовольствия 😈🔥"
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
            persona = male_personas[i % len(male_personas)]
            name = random.choice(MALE_NAMES) if i % 2 == 0 else persona.name
            age = random.randint(20, 42)
            city = random.choice(CITIES)
            bio = random.choice(MALE_BIOS)
            target = random.choices(["female", "couple", "all"], weights=[80, 10, 10])[0]
            created_at = now - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))

            existing_user = (await session.execute(select(User).where(User.telegram_id == tg_id))).scalar_one_or_none()
            if existing_user:
                existing_user.bio = bio
                existing_user.is_active = True
                existing_user.is_banned = False
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
            persona = female_personas[i % len(female_personas)]
            name = random.choice(FEMALE_NAMES) if i % 2 == 0 else persona.name
            age = random.randint(18, 38)
            city = random.choice(CITIES)
            bio = random.choice(FEMALE_BIOS)
            target = random.choices(["male", "couple", "all"], weights=[80, 10, 10])[0]
            created_at = now - timedelta(days=random.randint(1, 30), hours=random.randint(0, 23))

            existing_user = (await session.execute(select(User).where(User.telegram_id == tg_id))).scalar_one_or_none()
            if existing_user:
                existing_user.bio = bio
                existing_user.is_active = True
                existing_user.is_banned = False
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

            existing_user = (await session.execute(select(User).where(User.telegram_id == tg_id))).scalar_one_or_none()
            if existing_user:
                existing_user.bio = bio
                existing_user.couple_age = couple_age
                existing_user.age = avg_age
                existing_user.is_active = True
                existing_user.is_banned = False
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
