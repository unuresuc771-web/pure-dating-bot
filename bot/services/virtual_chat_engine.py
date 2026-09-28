import asyncio
import logging
import random
import re
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple
from aiogram import Bot
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import User, ChatSession, ChatMessage, utc_now
from bot.services.chat_service import ChatService
from bot.services.admin_service import AdminService
from bot.keyboards.reply import get_main_keyboard

logger = logging.getLogger(__name__)

# Архетипы личности для виртуальных пользователей
ARCHETYPES = {
    "female": ["coquette", "seductress", "mysterious"],
    "male": ["alpha", "rebel"],
    "couple": ["open_couple"]
}

# Тематические банки реплик по стадиям (1–10)
# Стадия 1: Приветствие и реакция на первый контакт
# Стадия 2: Вайб города и контекст (город, планы, настроение)
# Стадия 3: Проверка раскованности и юмора
# Стадия 4: Легкий флирт и комплименты
# Стадия 5: Углубление темы / интригующие вопросы
# Стадия 6: Проверка на спонтанность
# Стадия 7: Откровенный флирт и намеки на влечение
# Стадия 8: Чувство химии и нетерпение к живому общению
# Стадия 9: Конкретное предложение встречи сегодня/ночью
# Стадия 10: Финальная интригующая фраза перед сжиганием чата

REPLIES = {
    # ------------------- ЖЕНСКИЕ АРХЕТИПЫ -------------------
    "coquette": {
        1: [
            "Привет) Как дела?",
            "Привет, чем занят?",
            "Привет) Ты свободен сегодня?",
            "Хей, как вечер проходит?"
        ],
        2: [
            "Ты в {city} сейчас?",
            "В каком районе живешь?",
            "Какие планы на вечер?",
            "Работаешь сегодня или отдыхаешь?"
        ],
        3: [
            "Понятно) А я дома сижу, скучно",
            "Ясно) Чем вообще по жизни занимаешься?",
            "Норм) Давно тут анкету завел?",
            "Хах, понятно) Я вот только зашла"
        ],
        4: [
            "Симпатичный ты по фото",
            "Приятно общаешься, без заскоков",
            "Мне нравится твой вайб",
            "Редко тут нормальные парни попадаются"
        ],
        5: [
            "Ты вообще за спонтанность?",
            "Любишь вино?",
            "Что вообще тут ищешь, если честно?",
            "Часто вот так знакомишься?"
        ],
        6: [
            "Не люблю долгие переписки, если честно",
            "По переписке все равно человека не поймешь",
            "Лучше один раз вживую увидеть, чем строчить",
            "Смысл днями писать сообщения, проще в реале"
        ],
        7: [
            "Ты мне нравишься",
            "Хочу тебя вживую увидеть",
            "Поехали куда-нибудь кофе выпьем или вина?",
            "У тебя есть время сегодня?"
        ],
        8: [
            "Давай увидимся сегодня?",
            "Слушай, давай встретимся, я свободна позже",
            "Я в центре сегодня, можно пересечься",
            "Ты на машине сегодня?"
        ],
        9: [
            "Давай так: скинь свой контакт или адрес, встретимся через часик",
            "Приезжай ко мне, вино есть. Ты как?",
            "Давай пересечемся на полчаса, поболтаем в машине или баре?",
            "Я свободна, давай увидимся прямо сейчас"
        ],
        10: [
            "Ладно, я чат удаляю, не люблю висеть в переписках) Если захочешь — найдешь еще тут 😉",
            "Всё, мне пора, чат закрываю. Увидимся в ленте, если судьба)",
            "Удаляю диалог, дела появились) Надеюсь, еще пересечемся!",
            "Закрываю чат, была рада поболтать. Пока)"
        ]
    },

    "seductress": {
        1: [
            "Привет. Как вечер?",
            "Привет, симпатичный. Чем занят?",
            "Привет. Ты сейчас свободен?",
            "Хей) Как настроение?"
        ],
        2: [
            "Ты в {city}?",
            "В каком районе обитаешь?",
            "Какие планы на ночь?",
            "Свободен сегодня или занят?"
        ],
        3: [
            "Поняла) А я вино пью одна",
            "Ясно. Люблю, когда без лишних слов",
            "Нормально) Давно в приложении?",
            "Хах, дерзко) Мне нравится"
        ],
        4: [
            "Хорошо выглядишь. Фигура отличная",
            "Приятный ты. Зацепил взглядом",
            "Уверенно пишешь, это привлекает",
            "Ты определенно в моем вкусе"
        ],
        5: [
            "Вино будешь?",
            "Ты легкий на подъем?",
            "Что ищешь здесь, если прямо?",
            "Секреты умеешь хранить?"
        ],
        6: [
            "Терпеть не могу долгие переписки ни о чем",
            "Вживую всё совсем по-другому чувствуется",
            "Зачем тратить время на текст, если можно встретиться",
            "Я за реал, чаты — это пустое"
        ],
        7: [
            "Ты меня привлекаешь",
            "Хочу увидеть тебя сегодня",
            "Давай перейдем к делу, без долгих прелюдий",
            "Чувствую, химия у нас будет отличная"
        ],
        8: [
            "Давай увидимся сегодня ночью",
            "Приезжай ко мне, посидим вдвоем",
            "Я свободна, давай пересечемся в центре",
            "Хватит переписываться, давай встретимся"
        ],
        9: [
            "Скинь контакт или адрес, встретимся через час. Ты за?",
            "Жду твой номер, наберу сейчас. Погнали ко мне",
            "Назови место, я подъеду. Вино с меня",
            "Я готова встретиться прямо сейчас. Поехали?"
        ],
        10: [
            "Чат сношу, долго не держу диалоги. Найдешь меня еще тут, если захочешь 😉",
            "Время вышло, удаляю переписку) До встречи в ленте!",
            "Всё, закрываю чат, дела. Рада была пообщаться, пока)"
        ]
    },

    "mysterious": {
        1: [
            "Привет... Чем занимаешься?",
            "Привет) Как твоя ночь?",
            "Привет. Ты сейчас не спишь?",
            "Хей... Как дела?"
        ],
        2: [
            "Ты в {city} сейчас?",
            "Любишь ночной город?",
            "Какие мысли на этот вечер?",
            "Дома сидишь или гуляешь?"
        ],
        3: [
            "Понятно... А я музыку слушаю, не спится",
            "Ясно. С тобой спокойно общаться",
            "Интересный ответ) Редко такие попадаются",
            "Хах, понятно... Улыбнуло)"
        ],
        4: [
            "У тебя очень приятный вайб",
            "Симпатичный на фото. Притягиваешь",
            "Мне нравится твой тон в тексте",
            "Кажется, у нас похожее настроение"
        ],
        5: [
            "Любишь вино под хорошую музыку?",
            "Ты веришь в случайные встречи?",
            "Что тебя сейчас больше всего расслабляет?",
            "Часто выбираешься спонтанно по ночам?"
        ],
        6: [
            "Не люблю долгие переписки, слова часто врут",
            "Вживую взгляд скажет больше любых сообщений",
            "Хочется увидеть тебя настоящего, без экранов",
            "Текст утомляет, живой разговор лучше"
        ],
        7: [
            "Ты мне правда нравишься...",
            "Хочу увидеть твои глаза вживую",
            "Давай выпьем где-нибудь в тихом месте?",
            "Ты свободен этой ночью?"
        ],
        8: [
            "Давай увидимся сегодня? Без лишних людей",
            "Приезжай на бокал вина, посидим поговорим",
            "Я свободна позже. Встретимся?",
            "Давай не откладывать, увидимся сегодня ночью"
        ],
        9: [
            "Напиши свой номер или куда подъехать, встретимся сегодня через полчаса",
            "Приезжай ко мне сегодня, адрес скину. Ты готов?",
            "Давай встретимся в центре прямо сейчас на кофе или вино",
            "Жду твой контакт, давай увидимся этой ночью"
        ],
        10: [
            "Ладно, удаляю чат... Не люблю висеть в сети. Найди меня снова, если захочешь 🌙",
            "Закрываю переписку, пора бежать. До встречи в ленте)",
            "Удаляю этот диалог, дела. Было приятно пообщаться... Пока)"
        ]
    },

    # ------------------- МУЖСКИЕ АРХЕТИПЫ -------------------
    "alpha": {
        1: [
            "Привет. Как дела?",
            "Привет, отлично выглядишь. Чем занята?",
            "Привет) Свободна сегодня вечером?",
            "Хей. Как вечер проходит?"
        ],
        2: [
            "Ты в {city} сейчас?",
            "В каком районе живешь?",
            "Какие планы на вечер?",
            "Работаешь сегодня или отдыхаешь?"
        ],
        3: [
            "Понял тебя) Люблю когда без лишних загонов",
            "Нормально) Давно в приложении?",
            "Ясно) Я вот только освободился по делам",
            "Хах, с юмором у тебя порядок 👍"
        ],
        4: [
            "Приятная ты. Фигура отличная",
            "Мне нравится твой стиль",
            "Симпатичная. В моем вкусе",
            "Редко тут нормальные девчонки попадаются"
        ],
        5: [
            "Вино пьешь?",
            "Ты вообще легкая на подъем?",
            "Что ищешь здесь, если честно?",
            "Как относишься к спонтанным встречам?"
        ],
        6: [
            "Не люблю долгие переписки ни о чем",
            "Лучше один раз вживую увидеть, чем неделю строчить",
            "По буквам человека не поймешь, надо вживую",
            "Я за реал, экран это не то"
        ],
        7: [
            "Ты мне понравилась, честно",
            "Хочу тебя увидеть сегодня",
            "Давай я за тобой заеду, посидим где-нибудь",
            "У меня номер в отеле, составишь компанию?"
        ],
        8: [
            "Слушай, давай не тянуть. Увидимся сегодня?",
            "Свободна через час? Заеду за тобой",
            "Погнали кофе выпьем или вина?",
            "Я сейчас в центре, давай пересечемся"
        ],
        9: [
            "Скинь свой контакт или адрес, я подъеду через 40 минут",
            "Давай адрес, заберу тебя. Посидим в приятном месте",
            "Жду твой номер, наберу сейчас",
            "Я свободен. Пиши куда подъехать"
        ],
        10: [
            "Ладно, чат сношу, не люблю копить переписки. Увидимся в ленте если что 😉",
            "Всё, закрываю чат, дела. Был рад пообщаться, пока)",
            "Удаляю диалог, долго не вишу. Если судьба — найдемся еще!"
        ]
    },

    "rebel": {
        1: [
            "Хей! Как дела?",
            "Привет) Чем занята прямо сейчас?",
            "Привет! Свободна сегодня?",
            "Здорово. Как настрой на вечер?"
        ],
        2: [
            "Ты в {city} сейчас?",
            "Где чаще бываешь в городе?",
            "Планы на ночь есть какие-то?",
            "Отдыхаешь сегодня?"
        ],
        3: [
            "Хах, кайф) Простой ответ, уважаю",
            "Ясно) Я вот только с тренировки / дел освободился",
            "Норм! С тобой легко общаться",
            "Ха, свой человек, чувствую)"
        ],
        4: [
            "Классная ты. Глаза цепляют",
            "Симпатичная, фигура 🔥",
            "Мне нравится твой вайб, без пафоса",
            "Редко такие интересные попадаются"
        ],
        5: [
            "Вино или кофе?",
            "На спонтанные вылазки готова?",
            "Что вообще ищешь здесь?",
            "Быстро с людьми сходишься?"
        ],
        6: [
            "Терпеть не могу строчить в чатах",
            "Лучше вживую увидеть, чем дни напролет писать",
            "В переписке всё не то, надо в реале",
            "Хватит сидеть в онлайне, надо жить"
        ],
        7: [
            "Ты мне понравилась",
            "Хочу тебя увидеть сегодня ночью",
            "Давай прокатимся по ночному городу?",
            "Погнали куда-нибудь, развеемся"
        ],
        8: [
            "Давай увидимся сегодня?",
            "Свободна через час? Подъеду",
            "Поехали выпьем чего-нибудь?",
            "Я в центре, давай пересечемся"
        ],
        9: [
            "Пиши адрес или контакт, заберу тебя через полчаса",
            "Давай номер, наберу. Поехали погуляем / в бар",
            "Жду адрес, заеду. Ты за?",
            "Я свободен прямо сейчас. Погнали?"
        ],
        10: [
            "Всё, чат закрываю, не люблю висеть в онлайне) Найдемся еще в поиске, пока!",
            "Удаляю переписку, дела. Рад был пообщаться!",
            "Сношу чат по правилам) Если что — лови меня в ленте 😉"
        ]
    },

    # ------------------- ПАРНЫЙ АРХЕТИП -------------------
    "open_couple": {
        1: [
            "Привет) Как дела?",
            "Привет! Мы пара, понравилась твоя анкета)",
            "Привет, свободна сегодня вечером?",
            "Хей! Чем занята сейчас?"
        ],
        2: [
            "Ты в {city} сейчас?",
            "В каком районе живешь?",
            "Какие планы на этот вечер?",
            "Отдыхаешь или работаешь?"
        ],
        3: [
            "Понятно) А мы вот дома сидим, вино открыли",
            "Ясно) Давно тут анкету завела?",
            "Приятно общаешься, легко",
            "Здорово, мы тоже за простой вайб"
        ],
        4: [
            "Ты очень симпатичная, нам обоим понравилась",
            "Приятный типаж у тебя",
            "Редко тут встретишь нормального человека",
            "У тебя классные фотки"
        ],
        5: [
            "Был опыт общения с парами?",
            "Вино любишь? Белое или красное?",
            "Что вообще ищешь здесь?",
            "Как относишься к встречам втроем?"
        ],
        6: [
            "Мы не любим долгие переписки",
            "В переписке всё равно не понять друг друга, лучше вживую",
            "Хочется вживую пообщаться, так проще",
            "Лучше сразу встретиться на полчаса"
        ],
        7: [
            "Очень хотим познакомиться вживую",
            "Ты нам правда понравилась",
            "Приезжай к нам на вино, просто поболтаем",
            "Давай пересечемся сегодня где-нибудь в тихом месте?"
        ],
        8: [
            "Свободна сегодня ночью? Мы в центре в апартаментах",
            "Давай увидимся сегодня? Вино уже охладили",
            "Поехали посидим где-нибудь, мы на машине",
            "Хватит переписываться, давай встретимся"
        ],
        9: [
            "Скинь контакт или адрес, вызовем такси к нам. Будет уютно и без напряга",
            "Давай адрес, заедем за тобой через полчаса",
            "Ждем твой тг или номер, спишемся и встретимся",
            "Приезжай прямо сейчас, мы свободны"
        ],
        10: [
            "Ладно, удаляем чат, не копим диалоги) Будем рады увидеться в ленте, пока!",
            "Чат закрываем, пора бежать. Было приятно поболтать!",
            "Удаляем переписку по правилам) Если что — ищи нас в поиске!"
        ]
    }
}


class VirtualChatEngine:
    """
    Интеллектуальный движок живых диалогов виртуальных пользователей:
    - 15% отклик на лайки
    - 10 сообщений диалога с развитием сюжета от знакомства до страстной интриги
    - Живая имитация набора текста
    - Авто-сжигание чата на 10 сообщении
    """

    @staticmethod
    def get_archetype_for_user(fake_user: User) -> str:
        """Определяет стабильный архетип для конкретного виртуального пользователя."""
        gender = fake_user.gender or "female"
        pool = ARCHETYPES.get(gender, ARCHETYPES["female"])
        idx = fake_user.id % len(pool)
        return pool[idx]

    @staticmethod
    async def should_match_back(session: AsyncSession, user_id: Optional[int] = None) -> bool:
        """
        Проверяет шанс отклика виртуала:
        - Базовая вероятность: 20% (0.20) или из настроек админки
        - Если лайков у пользователя мало, шанс адаптивно увеличивается (до 80%), чтобы вовлечь новичка
        - Каждый 5-й лайк (likes_count % 5 == 0) — гарантированный взаимный отклик (100%)
        """
        base_rate = await AdminService.get_virtual_match_rate(session)
        if user_id is None:
            return random.random() < base_rate

        from bot.database.models import Reaction
        stmt = select(func.count(Reaction.id)).where(
            Reaction.from_user_id == user_id,
            Reaction.reaction_type == "like"
        )
        total_likes = (await session.execute(stmt)).scalar() or 0

        # Адаптивное увеличение шанса для новичков ("Если лайков меньше, то процент может увеличиваться"):
        if total_likes <= 1:
            effective_rate = 0.80  # 1-й лайк: 80% шанс отклика
        elif total_likes == 2:
            effective_rate = 0.60  # 2-й лайк: 60%
        elif total_likes == 3:
            effective_rate = 0.40  # 3-й лайк: 40%
        elif total_likes == 4:
            effective_rate = 0.30  # 4-й лайк: 30%
        else:
            # "Каждый пятый лайк пускай отвечает и ведёт диалог"
            if total_likes % 5 == 0:
                effective_rate = 1.0
            else:
                effective_rate = base_rate

        return random.random() < effective_rate

    @staticmethod
    async def count_virtual_messages_in_session(session: AsyncSession, session_id: int, virtual_user_id: int) -> int:
        """Считает, сколько сообщений виртуальный пользователь уже отправил в этой сессии."""
        stmt = select(func.count(ChatMessage.id)).where(
            ChatMessage.session_id == session_id,
            ChatMessage.sender_id == virtual_user_id
        )
        res = await session.execute(stmt)
        return res.scalar() or 0

    @staticmethod
    def generate_reply(
        stage: int,
        archetype: str,
        user: User,
        fake_user: User,
        user_message_text: str = ""
    ) -> str:
        """
        Генерирует умную нешаблонную реплику с учетом контекста, города, возраста и стадии диалога.
        """
        stage = max(1, min(10, stage))
        gender_dict = REPLIES.get(archetype)
        if not gender_dict:
            # Fallback
            gender_dict = REPLIES["coquette"]

        options = gender_dict.get(stage, gender_dict[1])
        base_template = random.choice(options)

        # Контекстные подстановки
        city_name = user.city or fake_user.city or "городе"
        reply = base_template.replace("{city}", city_name)

        # Естественные модификаторы (случайный нижний регистр первого слова, естественные междометия)
        if random.random() < 0.25 and not reply.startswith("Привет") and not reply.startswith("Хей"):
            reply = reply[0].lower() + reply[1:]

        return reply

    @staticmethod
    async def process_virtual_reply(
        bot: Bot,
        session_id: int,
        real_user: User,
        fake_user: User,
        user_message_text: str = ""
    ):
        """
        Асинхронный фоновый воркер:
        1. Имитирует чтение и паузу размышления человека.
        2. Отправляет статус typing в Telegram.
        3. Отправляет реалистичный ответ.
        4. Если это 10-е сообщение — ожидает 6 секунд и полностью сжигает чат!
        """
        try:
            # 1. Реалистичная задержка чтения сообщения (4.0 - 9.0 сек)
            thinking_delay = random.uniform(4.0, 9.0)
            await asyncio.sleep(thinking_delay)

            # 2. Вычисляем текущую стадию диалога
            from bot.database.db import async_session_maker
            async with async_session_maker() as session:
                chat = await ChatService.get_session_by_id(session, session_id)
                if not chat or chat.status != "active":
                    return

                prev_count = await VirtualChatEngine.count_virtual_messages_in_session(
                    session=session,
                    session_id=session_id,
                    virtual_user_id=fake_user.id
                )
                stage = prev_count + 1

                archetype = VirtualChatEngine.get_archetype_for_user(fake_user)
                reply_text = VirtualChatEngine.generate_reply(
                    stage=stage,
                    archetype=archetype,
                    user=real_user,
                    fake_user=fake_user,
                    user_message_text=user_message_text
                )

            # 3. Имитация набора текста
            typing_duration = min(4.5, max(1.8, len(reply_text) * 0.05))
            try:
                await bot.send_chat_action(chat_id=real_user.telegram_id, action="typing")
            except Exception as e:
                logger.debug(f"Failed to send typing action: {e}")

            await asyncio.sleep(typing_duration)

            # 4. Отправка сообщения
            async with async_session_maker() as session:
                chat = await ChatService.get_session_by_id(session, session_id)
                if not chat or chat.status != "active":
                    return

                # Проверяем, активен ли чат на экране у пользователя
                db_user = await session.get(User, real_user.id)
                user_in_chat = (db_user and db_user.active_chat_id == chat.id)
                from bot.keyboards.inline import get_new_message_alert_keyboard
                reply_markup = None if user_in_chat else get_new_message_alert_keyboard(chat.id, partner_name=fake_user.first_name)

                sent_msg = await bot.send_message(
                    chat_id=real_user.telegram_id,
                    text=f"<b>{fake_user.first_name}:</b> {reply_text}",
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )

                if sent_msg:
                    await ChatService.record_relayed_message(
                        session=session,
                        session_id=chat.id,
                        sender_id=fake_user.id,
                        sender_message_id=sent_msg.message_id,
                        recipient_message_id=sent_msg.message_id,
                        text=reply_text,
                        media_type="text"
                    )

            # 5. Если это стадия 10 — кульминация и авто-сжигание диалога!
            if stage >= 10:
                logger.info(f"Virtual chat {session_id} reached stage {stage}. Scheduling burn in 6 seconds...")
                await asyncio.sleep(6.0)

                async with async_session_maker() as session:
                    success, u_a, u_b = await ChatService.burn_and_close_chat(
                        bot=bot,
                        session=session,
                        session_id=session_id,
                        closed_by_user_id=fake_user.id
                    )

                    if success:
                        try:
                            await bot.send_message(
                                chat_id=real_user.telegram_id,
                                text=(
                                    "💥 <b>Собеседник завершил и сжёг чат.</b>\n\n"
                                    "По правилам сервиса Pure вся переписка стёрта без следа.\n"
                                    "<i>Ищите новые совпадения в ленте — возможно, вы встретитесь снова! 😉</i>"
                                ),
                                reply_markup=get_main_keyboard(),
                                parse_mode="HTML"
                            )
                        except Exception as e:
                            logger.error(f"Failed to notify user of burned virtual chat: {e}")

        except Exception as e:
            logger.error(f"Error in process_virtual_reply for session {session_id}: {e}", exc_info=True)

    @staticmethod
    def schedule_delayed_match(
        bot: Bot,
        real_user_id: int,
        fake_user_id: int,
        min_delay: int = 25,
        max_delay: int = 70
    ):
        """
        Запускает отложенный взаимный отклик от виртуала через реалистичную паузу.
        Человек не отвечает сиюсекундно — создаётся полное ощущение,
        что живой собеседник увидел уведомление о лайке, открыл профиль и ответил взаимностью.
        """
        asyncio.create_task(
            VirtualChatEngine._execute_delayed_match(
                bot=bot,
                real_user_id=real_user_id,
                fake_user_id=fake_user_id,
                min_delay=min_delay,
                max_delay=max_delay
            )
        )

    @staticmethod
    async def _execute_delayed_match(
        bot: Bot,
        real_user_id: int,
        fake_user_id: int,
        min_delay: int = 25,
        max_delay: int = 70
    ):
        delay = random.randint(min_delay, max_delay)
        logger.info(f"Scheduled delayed virtual match: real_user={real_user_id}, fake_user={fake_user_id} in {delay}s")
        await asyncio.sleep(delay)

        from bot.database.db import async_session_maker
        from bot.keyboards.inline import get_match_keyboard
        from bot.services.avatar_cache import AvatarCacheService
        from bot.database.models import Reaction, Match

        async with async_session_maker() as session:
            real_user = await session.get(User, real_user_id)
            fake_user = await session.get(User, fake_user_id)
            if not real_user or not fake_user or not real_user.is_active or real_user.is_banned:
                return

            # Проверяем, нет ли уже матча
            u1, u2 = min(real_user_id, fake_user_id), max(real_user_id, fake_user_id)
            m_check = await session.execute(
                select(Match).where(Match.user1_id == u1, Match.user2_id == u2)
            )
            if m_check.scalar_one_or_none():
                return

            # Создаем взаимный лайк от виртуала
            fake_reaction = Reaction(
                from_user_id=fake_user_id,
                to_user_id=real_user_id,
                reaction_type="like",
                created_at=utc_now()
            )
            session.add(fake_reaction)
            session.add(Match(user1_id=u1, user2_id=u2, created_at=utc_now()))
            await session.commit()

            # Создаем сессию чата
            chat_session = await ChatService.create_or_get_session(session, real_user_id, fake_user_id)

            # Отправляем красивое пуш-уведомление с фото собеседника в Telegram
            try:
                text = (
                    f"🎉 <b>Взаимная симпатия с {fake_user.first_name}!</b>\n\n"
                    f"Собеседник только что оценил вашу анкету в ответ.\n"
                    "Начните анонимный диалог прямо сейчас:"
                )
                await AvatarCacheService.send_avatar_photo(
                    bot=bot,
                    chat_id=real_user.telegram_id,
                    avatar_path=fake_user.avatar_path,
                    is_custom_photo=fake_user.is_custom_photo,
                    caption=text,
                    reply_markup=get_match_keyboard(chat_session.id)
                )
            except Exception as e:
                logger.error(f"Failed to send delayed match alert: {e}")
                try:
                    await bot.send_message(
                        chat_id=real_user.telegram_id,
                        text=(
                            f"🎉 <b>Взаимная симпатия с {fake_user.first_name}!</b>\n\n"
                            f"Собеседник только что оценил вашу анкету в ответ.\n"
                            "Начните анонимный диалог прямо сейчас:"
                        ),
                        reply_markup=get_match_keyboard(chat_session.id),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
