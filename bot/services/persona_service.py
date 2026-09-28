import os
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class Persona:
    id: str
    num: int
    gender: str
    name: str
    en_name: str
    avatar_path: str
    pattern: str
    palette_name: str
    colors: Tuple[str, str]

# Реестр 18 готовых мужских образов из Sep 27 - 10_32 с русскими надписями
MALE_PERSONAS: List[Persona] = [
    Persona(
        id="m_01",
        num=1,
        gender="male",
        name="Ночной Демон",
        en_name="Night Demon",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_01.jpg"),
        pattern="Оптический вортекс и спиральные лучи",
        palette_name="Розовый Pure & Неоновый Оранж",
        colors=("#FF007F", "#FF5500")
    ),
    Persona(
        id="m_02",
        num=2,
        gender="male",
        name="Грешный Ангел",
        en_name="Sinful Angel",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_02.jpg"),
        pattern="Искаженная оптическая шахматка",
        palette_name="Электрический Фиолет & Неоновый Лимон",
        colors=("#8A2BE2", "#FAFF00")
    ),
    Persona(
        id="m_03",
        num=3,
        gender="male",
        name="Безумный Кролик",
        en_name="Mad Rabbit",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_03.jpg"),
        pattern="Плавящиеся ацид-капли лава-лампы",
        palette_name="Токсичный Лайм & Глубокая Фуксия",
        colors=("#39FF14", "#FF007F")
    ),
    Persona(
        id="m_06",
        num=6,
        gender="male",
        name="Сладкий Яд",
        en_name="Sweet Poison",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_06.jpg"),
        pattern="Жидкий психоделический мрамор",
        palette_name="Изумрудный Неон & Королевский Пурпур",
        colors=("#00FF87", "#6000FF")
    ),
    Persona(
        id="m_07",
        num=7,
        gender="male",
        name="Космический Монстр",
        en_name="Cosmic Monster",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_07.jpg"),
        pattern="Астральные лучи и вспышка сверхновой",
        palette_name="Астральный Индиго & Неоновый Розовый",
        colors=("#3D00FF", "#FF00B8")
    ),
    Persona(
        id="m_08",
        num=8,
        gender="male",
        name="Лукавый Лис",
        en_name="Sly Fox",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_08.jpg"),
        pattern="Оптические тигровые и зебровые волны",
        palette_name="Огненный Янтарь & Электрический Кобальт",
        colors=("#FF5100", "#0055FF")
    ),
    Persona(
        id="m_09",
        num=9,
        gender="male",
        name="Дикий Зверь",
        en_name="Wild Beast",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_09.jpg"),
        pattern="Топографические изометрические кривые высот",
        palette_name="Солнечное Золото & Рубиновый Багрянец",
        colors=("#FFD700", "#D90429")
    ),
    Persona(
        id="m_10",
        num=10,
        gender="male",
        name="Огненный Бунтарь",
        en_name="Fiery Rebel",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_10.jpg"),
        pattern="Электрические разряды молний",
        palette_name="Пламенный Алый & Неоновая Аква",
        colors=("#FF2200", "#00F0FF")
    ),
    Persona(
        id="m_11",
        num=11,
        gender="male",
        name="Тайный Искуситель",
        en_name="Secret Tempter",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_11.jpg"),
        pattern="Оптический туннель замочных скважин",
        palette_name="Аметистовый Фиолет & Медовое Золото",
        colors=("#7209B7", "#FFB703")
    ),
    Persona(
        id="m_12",
        num=12,
        gender="male",
        name="Бархатный Чёрт",
        en_name="Velvet Imp",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_12.jpg"),
        pattern="Поп-арт точки Бен-Дей",
        palette_name="Глубокий Кармин & Мятный Щербет",
        colors=("#E01A4F", "#0CF574")
    ),
    Persona(
        id="m_13",
        num=13,
        gender="male",
        name="Мрачный Романтик",
        en_name="Dark Romantic",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_13.jpg"),
        pattern="Крылья летучих мышей и полумесяцы",
        palette_name="Полуночный Сапфир & Пудровая Роза",
        colors=("#1B1B3A", "#FF85A1")
    ),
    Persona(
        id="m_14",
        num=14,
        gender="male",
        name="Пьяный Сатир",
        en_name="Drunken Satyr",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_14.jpg"),
        pattern="Спиральные виноградные лозы",
        palette_name="Электрический Виноград & Спелый Апельсин",
        colors=("#9D4EDD", "#FF9E00")
    ),
    Persona(
        id="m_15",
        num=15,
        gender="male",
        name="Дерзкий Фавн",
        en_name="Bold Faun",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_15.jpg"),
        pattern="Оптические годовые кольца дерева",
        palette_name="Изумрудная Бирюза & Темная Слива",
        colors=("#00F5D4", "#7B2CBF")
    ),
    Persona(
        id="m_16",
        num=16,
        gender="male",
        name="Ночной Охотник",
        en_name="Night Hunter",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_16.jpg"),
        pattern="Стелс-сетка сот ниндзя",
        palette_name="Глубокая Тень & Кислотный Лайм",
        colors=("#0A1128", "#70E000")
    ),
    Persona(
        id="m_17",
        num=17,
        gender="male",
        name="Мистический Бес",
        en_name="Mystic Imp",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_17.jpg"),
        pattern="Калейдоскопическая мандала",
        palette_name="Кибер-Фуксия & Мятная Бирюза",
        colors=("#FF0055", "#00FFA3")
    ),
    Persona(
        id="m_18",
        num=18,
        gender="male",
        name="Грешник без вины",
        en_name="Guiltless Sinner",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_18.jpg"),
        pattern="Плавящиеся оптические поп-арт сердца",
        palette_name="Алый Кардинал & Арктический Лед",
        colors=("#E63946", "#A8DADC")
    ),
    Persona(
        id="m_19",
        num=19,
        gender="male",
        name="Теневой Идол",
        en_name="Shadow Idol",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_19.jpg"),
        pattern="Ацтекский ступенчатый меандр",
        palette_name="Теневой Графит & Закатный Янтарь",
        colors=("#1D2A44", "#FF9F1C")
    ),
    Persona(
        id="m_20",
        num=20,
        gender="male",
        name="Электрический Демон",
        en_name="Electric Demon",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "male", "male_20.jpg"),
        pattern="Пульсирующие звуковые волны эквалайзера",
        palette_name="Молниеносный Желтый & Кибер-Пурпур",
        colors=("#FFE600", "#480CA8")
    ),
]

# Реестр 20 готовых женских образов из Sep 27 - 10_32 с русскими надписями
FEMALE_PERSONAS: List[Persona] = [
    Persona(
        id="f_01",
        num=1,
        gender="female",
        name="Маленькая Чертовка",
        en_name="Little She-Devil",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_01.jpg"),
        pattern="Оптические волны зебры",
        palette_name="Горячий Розовый & Солнечный Оранж",
        colors=("#FF007F", "#FF7700")
    ),
    Persona(
        id="f_02",
        num=2,
        gender="female",
        name="Дикая Кошка",
        en_name="Wild Cat",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_02.jpg"),
        pattern="Концентрические миндалевидные кошачьи глаза",
        palette_name="Неоновый Аквамарин & Электрическая Фуксия",
        colors=("#00F5D4", "#F72585")
    ),
    Persona(
        id="f_03",
        num=3,
        gender="female",
        name="Сладкая Ведьма",
        en_name="Sweet Witch",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_03.jpg"),
        pattern="Спиральная паутина и лунные фазы",
        palette_name="Кибер-Пурпур & Кислотный Лайм",
        colors=("#7209B7", "#CCFF00")
    ),
    Persona(
        id="f_04",
        num=4,
        gender="female",
        name="Грешная Нимфа",
        en_name="Sinful Nymph",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_04.jpg"),
        pattern="Психоделические ромашки и лепестки 60-х",
        palette_name="Изумрудный Лес & Яркий Коралл",
        colors=("#065A38", "#FF5E7E")
    ),
    Persona(
        id="f_05",
        num=5,
        gender="female",
        name="Ночная Бестия",
        en_name="Night Beast",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_05.jpg"),
        pattern="Оптические арки крыльев летучей мыши",
        palette_name="Глубокий Индиго & Пламенный Оранж",
        colors=("#240046", "#FF5400")
    ),
    Persona(
        id="f_06",
        num=6,
        gender="female",
        name="Кибер Суккуб",
        en_name="Cyber Succubus",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_06.jpg"),
        pattern="Изометрическая кибер-сетка Трон",
        palette_name="Неоновый Циан & Горячая Маджента",
        colors=("#00E5FF", "#FF007F")
    ),
    Persona(
        id="f_07",
        num=7,
        gender="female",
        name="Опасная Малышка",
        en_name="Dangerous Babe",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_07.jpg"),
        pattern="Оптические гипнотические ромбы Арлекина",
        palette_name="Кровавый Кардинал & Электрический Тил",
        colors=("#D00000", "#03CEA4")
    ),
    Persona(
        id="f_08",
        num=8,
        gender="female",
        name="Ядовитая Мята",
        en_name="Poison Mint",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_08.jpg"),
        pattern="Жидкие щупальца медузы и пузыри",
        palette_name="Светящаяся Мята & Темная Ежевика",
        colors=("#00FFC6", "#4A0E4E")
    ),
    Persona(
        id="f_09",
        num=9,
        gender="female",
        name="Мятежная Душа",
        en_name="Rebel Soul",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_09.jpg"),
        pattern="Анархистский оптический калейдоскоп",
        palette_name="Неоновый Мандарин & Ультрамарин",
        colors=("#FF6000", "#2B00FF")
    ),
    Persona(
        id="f_10",
        num=10,
        gender="female",
        name="Лунная Сирена",
        en_name="Lunar Siren",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_10.jpg"),
        pattern="Морские волны и ракушки Наутилус",
        palette_name="Океанский Индиго & Жемчужная Бирюза",
        colors=("#0B1354", "#00F2FE")
    ),
    Persona(
        id="f_11",
        num=11,
        gender="female",
        name="Бархатная Пантера",
        en_name="Velvet Panther",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_11.jpg"),
        pattern="Искаженный жидкий леопардовый принт",
        palette_name="Королевский Вельвет & Золотистый Янтарь",
        colors=("#3A0CA3", "#FFB703")
    ),
    Persona(
        id="f_12",
        num=12,
        gender="female",
        name="Искренняя Дьяволица",
        en_name="Sincere She-Devil",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_12.jpg"),
        pattern="Поп-арт калейдоскоп бесконечных сердец",
        palette_name="Сияющая Фуксия & Солнечный Желтый",
        colors=("#FF006E", "#FFBE0B")
    ),
    Persona(
        id="f_13",
        num=13,
        gender="female",
        name="Розовая Фурия",
        en_name="Pink Fury",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_13.jpg"),
        pattern="Оптические языки яростного пламени",
        palette_name="Пылающий Неоновый Розовый & Яркий Салат",
        colors=("#FF1493", "#00FF66")
    ),
    Persona(
        id="f_14",
        num=14,
        gender="female",
        name="Пылающая Медуза",
        en_name="Blazing Medusa",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_14.jpg"),
        pattern="Гипнотический змеиный лабиринт",
        palette_name="Огненный Алый & Неоновый Циан",
        colors=("#FF2A00", "#00FFFF")
    ),
    Persona(
        id="f_15",
        num=15,
        gender="female",
        name="Космическая Киска",
        en_name="Cosmic Kitty",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_15.jpg"),
        pattern="Кольца Сатурна и кометные хвосты",
        palette_name="Космическая Лаванда & Бабл-Гам Розовый",
        colors=("#8338EC", "#FF66C4")
    ),
    Persona(
        id="f_16",
        num=16,
        gender="female",
        name="Чертовски Милая",
        en_name="Hellishly Sweet",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_16.jpg"),
        pattern="Оптические шахматные сердечки",
        palette_name="Коралловый Персик & Глубокий Индиго",
        colors=("#FF8C7A", "#0B2545")
    ),
    Persona(
        id="f_17",
        num=17,
        gender="female",
        name="Запретный Плод",
        en_name="Forbidden Fruit",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_17.jpg"),
        pattern="Оптические срезы сочных яблок",
        palette_name="Кровавая Вишня & Неоновый Шартрез",
        colors=("#9A031E", "#E36414")
    ),
    Persona(
        id="f_18",
        num=18,
        gender="female",
        name="Тайная Грешница",
        en_name="Secret Sinner",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_18.jpg"),
        pattern="Готические витражные стрельчатые арки",
        palette_name="Темный Плум & Розовое Золото",
        colors=("#560BAD", "#F77F00")
    ),
    Persona(
        id="f_19",
        num=19,
        gender="female",
        name="Дерзкая Искусительница",
        en_name="Bold Temptress",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_19.jpg"),
        pattern="Венецианский складной веер и шелковые ленты",
        palette_name="Рубиновый Бархат & Яркое Золото",
        colors=("#BA181B", "#FFD166")
    ),
    Persona(
        id="f_20",
        num=20,
        gender="female",
        name="Огненная Бестия",
        en_name="Fiery Vixen",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "female", "female_20.jpg"),
        pattern="Японские волны Сейгайха и огненные искры",
        palette_name="Пламенный Оранж & Электрическая Маджента",
        colors=("#FF3C00", "#B5179E")
    ),
]

# Реестр 20 парных образов
COUPLE_PERSONAS: List[Persona] = [
    Persona(
        id="c_01",
        num=1,
        gender="couple",
        name="Опасный Дуэт",
        en_name="Dangerous Duo",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_01.jpg"),
        pattern="Оптический туннель замочных скважин",
        palette_name="Маджента Pure & Неоновый Циан",
        colors=("#FF007F", "#00F0FF")
    ),
    Persona(
        id="c_02",
        num=2,
        gender="couple",
        name="Бонни и Клайд",
        en_name="Bonnie & Clyde",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_02.jpg"),
        pattern="Искаженная оптическая шахматка",
        palette_name="Электрический Фиолет & Неоновый Лимон",
        colors=("#8A2BE2", "#FAFF00")
    ),
    Persona(
        id="c_03",
        num=3,
        gender="couple",
        name="Дикая Любовь",
        en_name="Wild Love",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_03.jpg"),
        pattern="Психоделические полосы зебры и тигра",
        palette_name="Горячий Розовый & Солнечный Оранж",
        colors=("#FF1493", "#FF6600")
    ),
    Persona(
        id="c_04",
        num=4,
        gender="couple",
        name="Ночные Хищники",
        en_name="Night Predators",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_04.jpg"),
        pattern="Концентрические кошачьи глаза",
        palette_name="Неоновый Изумруд & Королевский Пурпур",
        colors=("#00FF87", "#6000FF")
    ),
    Persona(
        id="c_05",
        num=5,
        gender="couple",
        name="Сладкий Грех",
        en_name="Sweet Sin",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_05.jpg"),
        pattern="Плавящиеся ацид-капли лава-лампы",
        palette_name="Токсичный Лайм & Глубокая Фуксия",
        colors=("#39FF14", "#FF007F")
    ),
    Persona(
        id="c_06",
        num=6,
        gender="couple",
        name="Тайный Союз",
        en_name="Secret Union",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_06.jpg"),
        pattern="Ступенчатый ацтекский лабиринт",
        palette_name="Астральный Индиго & Неоновый Розовый",
        colors=("#3D00FF", "#FF00B8")
    ),
    Persona(
        id="c_07",
        num=7,
        gender="couple",
        name="Электрическая Пара",
        en_name="Electric Pair",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_07.jpg"),
        pattern="Пульсирующие звуковые волны",
        palette_name="Молниеносный Желтый & Кибер-Пурпур",
        colors=("#FFE600", "#480CA8")
    ),
    Persona(
        id="c_08",
        num=8,
        gender="couple",
        name="Грешный Рай",
        en_name="Sinful Paradise",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_08.jpg"),
        pattern="Плавящиеся оптические поп-арт сердца",
        palette_name="Алый Кардинал & Мятный Арктический Неон",
        colors=("#E63946", "#A8DADC")
    ),
    Persona(
        id="c_09",
        num=9,
        gender="couple",
        name="Двойной Соблазн",
        en_name="Double Temptation",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_09.jpg"),
        pattern="Оптическая спираль гипноза",
        palette_name="Пылающий Коралл & Глубокий Ультрамарин",
        colors=("#FF3366", "#3333FF")
    ),
    Persona(
        id="c_10",
        num=10,
        gender="couple",
        name="Теневой Альянс",
        en_name="Shadow Alliance",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_10.jpg"),
        pattern="Кибер-лабиринт и печатные платы",
        palette_name="Кибер-Циан & Неоновый Мандарин",
        colors=("#05D9E8", "#FF6C00")
    ),
    Persona(
        id="c_11",
        num=11,
        gender="couple",
        name="В ритме Танго",
        en_name="Tango Rhythm",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_11.jpg"),
        pattern="Ретро-шевроны и зигзаги 70-х",
        palette_name="Рубиновый Неон & Бирюзовая Волна",
        colors=("#FF2A6D", "#00F0FF")
    ),
    Persona(
        id="c_12",
        num=12,
        gender="couple",
        name="Пылкий Джаз",
        en_name="Fiery Jazz",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_12.jpg"),
        pattern="Астральные вспышки и лучи",
        palette_name="Золотой Неон & Темный Пурпур Ночи",
        colors=("#FFD700", "#1A0933")
    ),
    Persona(
        id="c_13",
        num=13,
        gender="couple",
        name="Неоновые Беглецы",
        en_name="Neon Runaways",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_13.jpg"),
        pattern="Жидкий психоделический мрамор",
        palette_name="Мятный Бирюзовый & Электрическая Фуксия",
        colors=("#00F5D4", "#F72585")
    ),
    Persona(
        id="c_14",
        num=14,
        gender="couple",
        name="Алая Страсть",
        en_name="Scarlet Passion",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_14.jpg"),
        pattern="Концентрические пульсирующие круги мишени",
        palette_name="Кроваво-Алый & Неоновый Персик",
        colors=("#FF0055", "#FFAA00")
    ),
    Persona(
        id="c_15",
        num=15,
        gender="couple",
        name="Темные Любовники",
        en_name="Dark Lovers",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_15.jpg"),
        pattern="Готический оп-арт орнамент Дамаск",
        palette_name="Ночной Сапфир & Розовый Флюор",
        colors=("#1B1B3A", "#FF36AB")
    ),
    Persona(
        id="c_16",
        num=16,
        gender="couple",
        name="Сумасшедший Тандем",
        en_name="Crazy Tandem",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_16.jpg"),
        pattern="Поп-арт точки полутона Лихтенштейна",
        palette_name="Ультрафиолет & Кислотный Лайм",
        colors=("#7928CA", "#50E3C2")
    ),
    Persona(
        id="c_17",
        num=17,
        gender="couple",
        name="Игры с Огнем",
        en_name="Playing with Fire",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_17.jpg"),
        pattern="Оптические вихри языков пламени",
        palette_name="Огненный Оранж & Желтый Электрик",
        colors=("#FF4500", "#FFD700")
    ),
    Persona(
        id="c_18",
        num=18,
        gender="couple",
        name="Кибер Влюбленные",
        en_name="Cyber Lovers",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_18.jpg"),
        pattern="Гексагональная сотовая сетка",
        palette_name="Матричный Неон-Зеленый & Глубокий Индиго",
        colors=("#00FF66", "#0B0033")
    ),
    Persona(
        id="c_19",
        num=19,
        gender="couple",
        name="Запретный Плод",
        en_name="Forbidden Fruit",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_19.jpg"),
        pattern="Психоделические тропические листья",
        palette_name="Горячий Амарант & Лаймовое Свечение",
        colors=("#E01E5A", "#A5FF00")
    ),
    Persona(
        id="c_20",
        num=20,
        gender="couple",
        name="Полночный Экспресс",
        en_name="Midnight Express",
        avatar_path=os.path.join(BASE_DIR, "assets", "avatars", "couple", "couple_20.jpg"),
        pattern="Перспективные скоростные лучи неонового тоннеля",
        palette_name="Неоновый Лазурит & Пурпурный Неон",
        colors=("#0070F3", "#F81CE5")
    ),
]

ALL_PERSONAS = MALE_PERSONAS + FEMALE_PERSONAS + COUPLE_PERSONAS

def get_personas_by_gender(gender: str) -> List[Persona]:
    """Возвращает список доступных образов по полу."""
    if gender == "female":
        return FEMALE_PERSONAS
    elif gender == "couple":
        return COUPLE_PERSONAS
    return MALE_PERSONAS

def get_random_persona(gender: str, exclude_name: Optional[str] = None) -> Persona:
    """Выбирает случайный образ для указанного пола (опционально исключая текущий)."""
    pool = get_personas_by_gender(gender)
    if exclude_name and len(pool) > 1:
        filtered = [p for p in pool if p.name != exclude_name]
        if filtered:
            return random.choice(filtered)
    return random.choice(pool)

def get_persona_by_id(persona_id: str) -> Optional[Persona]:
    """Находит образ по ID (напр. 'm_01', 'f_07' или 'c_03')."""
    for p in ALL_PERSONAS:
        if p.id == persona_id:
            return p
    return None

def get_persona_by_name(name: str, gender: Optional[str] = None) -> Optional[Persona]:
    """Находит образ по его точному русскому имени."""
    pool = get_personas_by_gender(gender) if gender else ALL_PERSONAS
    for p in pool:
        if p.name.strip().lower() == name.strip().lower():
            return p
    return None

def get_persona_by_avatar(avatar_path: str) -> Optional[Persona]:
    """Находит образ по пути к аватарке."""
    norm_path = os.path.normpath(avatar_path)
    for p in ALL_PERSONAS:
        if os.path.normpath(p.avatar_path) == norm_path or os.path.basename(p.avatar_path) == os.path.basename(avatar_path):
            return p
    return None

