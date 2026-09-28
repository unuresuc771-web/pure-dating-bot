import html
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from bot.database.db import async_session_maker
from bot.services.admin_service import AdminService
from bot.services.seed_service import SeedService
from bot.states.admin import AdminLoginStates, AdminSettingsStates
from bot.keyboards.admin import (
    get_admin_main_keyboard,
    get_admin_back_keyboard,
    get_bots_management_keyboard
)

router = Router(name="admin_panel")

async def render_main_admin_menu(session, message: Message, is_edit: bool = False):
    stats = await AdminService.get_analytics_summary(session)
    pass_status = "🟢 ВКЛЮЧЕН" if stats["pass_enabled"] else "🔴 ВЫКЛЮЧЕН"
    cur_pass = f" (пароль: <code>{html.escape(stats['pass_val'])}</code>)" if stats["pass_enabled"] and stats["pass_val"] else ""

    text = (
        "👑 <b>Кабинет администратора Pure</b>\n\n"
        f"• Всего пользователей в базе: <b>{stats['total_users']}</b>\n"
        f"  └ Живых: <b>{stats['real_users']}</b> | Ботов: <b>{stats['fake_users']}</b>\n"
        f"• Онлайн прямо сейчас: <b>{stats['online_now']} чел.</b>\n"
        f"• Заходов сегодня (DAU): <b>{stats['dau']} чел.</b>\n"
        f"• Среднее время в боте: <b>{stats['avg_visit_min']} мин.</b>\n"
        f"• Активных чатов сейчас: <b>{stats['active_chats']}</b>\n"
        f"• Доступ по паролю: <b>{pass_status}</b>{cur_pass}\n\n"
        "<i>Выберите интересующий раздел:</i>"
    )

    markup = get_admin_main_keyboard(stats["pass_enabled"])
    if is_edit:
        try:
            await message.edit_text(text, reply_markup=markup, parse_mode="HTML")
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=markup, parse_mode="HTML")

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    async with async_session_maker() as session:
        # 1. Проверяем Telegram ID
        if AdminService.is_admin_id(message.from_user.id):
            await state.clear()
            await render_main_admin_menu(session, message, is_edit=False)
            return

        # 2. Если ID нет в списке, проверяем авторизацию в FSM или запрашиваем пароль
        data = await state.get_data()
        if data.get("is_admin_authenticated"):
            await render_main_admin_menu(session, message, is_edit=False)
            return

        await state.set_state(AdminLoginStates.password)
        await message.answer(
            "🔒 <b>Вход в кабинет администратора</b>\n\n"
            "Ваш Telegram ID не найден в списке доверенных администраторов.\n"
            "Пожалуйста, введите пароль администратора:",
            parse_mode="HTML"
        )

@router.message(AdminLoginStates.password, F.text)
async def process_admin_password(message: Message, state: FSMContext):
    password_input = message.text.strip()
    async with async_session_maker() as session:
        valid = await AdminService.verify_admin_password(session, password_input)
        if valid:
            await state.update_data(is_admin_authenticated=True)
            await message.answer("✅ Авторизация успешна!")
            await render_main_admin_menu(session, message, is_edit=False)
        else:
            await message.answer("❌ Неверный пароль администратора. Попробуйте еще раз:")

@router.callback_query(F.data.in_({"adm_view:main", "adm_view:refresh"}))
async def cb_admin_main(call: CallbackQuery):
    await call.answer()
    async with async_session_maker() as session:
        await render_main_admin_menu(session, call.message, is_edit=True)

@router.callback_query(F.data == "adm_view:summary")
async def cb_admin_summary(call: CallbackQuery):
    await call.answer()
    async with async_session_maker() as session:
        s = await AdminService.get_analytics_summary(session)
        text = (
            "📊 <b>Сводная аналитика Pure Match</b>\n\n"
            f"👥 <b>Пользователи:</b>\n"
            f"• Всего анкет: <b>{s['total_users']}</b>\n"
            f"• Реальных людей: <b>{s['real_users']}</b>\n"
            f"• Виртуальных профилей: <b>{s['fake_users']}</b>\n"
            f"• Новых за 24 часа: <b>+{s['new_24h']}</b>\n"
            f"• Новых за 7 дней: <b>+{s['new_7d']}</b>\n\n"
            f"📈 <b>Активность аудитории:</b>\n"
            f"• Онлайн прямо сейчас: <b>{s['online_now']}</b>\n"
            f"• DAU (активных сегодня): <b>{s['dau']}</b>\n"
            f"• WAU (активных за 7 дней): <b>{s['wau']}</b>\n"
            f"• MAU (активных за 30 дней): <b>{s['mau']}</b>\n"
            f"• Среднее время в боте: <b>{s['avg_visit_min']} мин/сессия</b>\n"
            f"• Всего сессий: <b>{s['total_visits']}</b>\n\n"
            f"💬 <b>Коммуникация:</b>\n"
            f"• Всего чатов: <b>{s['total_chats']}</b> (активных: {s['active_chats']})\n"
            f"• Сообщений отправлено: <b>{s['total_msgs']}</b> (за 24ч: {s['msgs_24h']})\n"
            f"• Секретных фото отправлено: <b>{s['total_secrets']}</b> (просмотрено: {s['viewed_secrets']})\n\n"
            f"❤️ <b>Симпатии и матчи:</b>\n"
            f"• Всего лайков: <b>{s['total_likes']}</b>\n"
            f"• Взаимных совпадений: <b>{s['total_matches']}</b>\n"
            f"• Match Rate (конверсия): <b>{s['match_rate']}%</b>\n\n"
            f"🛡 <b>Безопасность:</b>\n"
            f"• Жалоб: <b>{s['total_reports']}</b> | В бане: <b>{s['banned_users']}</b>"
        )
        await call.message.edit_text(text, reply_markup=get_admin_back_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "adm_view:activity")
async def cb_admin_activity(call: CallbackQuery):
    await call.answer()
    async with async_session_maker() as session:
        s = await AdminService.get_analytics_summary(session)
        text = (
            "⏱ <b>Аналитика активности и вовлеченности:</b>\n\n"
            f"• 🟢 <b>Онлайн сейчас (15 мин):</b> {s['online_now']} пользователей\n"
            f"• 📅 <b>DAU (уникальных сегодня):</b> {s['dau']} чел.\n"
            f"• 📅 <b>WAU (уникальных за неделю):</b> {s['wau']} чел.\n"
            f"• 📅 <b>MAU (уникальных за месяц):</b> {s['mau']} чел.\n\n"
            f"• ⏳ <b>Среднее время захода:</b> ~{s['avg_visit_min']} минут\n"
            f"• 🚪 <b>Всего сессий входа:</b> {s['total_visits']}\n"
            f"• ⚡️ <b>Новых регистраций за сутки:</b> +{s['new_24h']}\n"
            f"• ⚡️ <b>Новых регистраций за 7 дней:</b> +{s['new_7d']}\n\n"
            "<i>Время фиксируется по активности пользователей в интерфейсе.</i>"
        )
        await call.message.edit_text(text, reply_markup=get_admin_back_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "adm_view:chats")
async def cb_admin_chats(call: CallbackQuery):
    await call.answer()
    async with async_session_maker() as session:
        s = await AdminService.get_analytics_summary(session)
        text = (
            "💬 <b>Аналитика чатов и диалогов:</b>\n\n"
            f"• Всего создано анонимных чатов: <b>{s['total_chats']}</b>\n"
            f"• Активных чатов прямо сейчас: <b>{s['active_chats']}</b>\n"
            f"• Всего переслано сообщений: <b>{s['total_msgs']}</b>\n"
            f"• Сообщений за последние 24 часа: <b>{s['msgs_24h']}</b>\n\n"
            f"📷 <b>Секретные самоуничтожающиеся фото:</b>\n"
            f"• Всего отправлено: <b>{s['total_secrets']}</b>\n"
            f"• Просмотрено и сгорело: <b>{s['viewed_secrets']}</b>\n"
            f"• Ожидают открытия: <b>{max(0, s['total_secrets'] - s['viewed_secrets'])}</b>"
        )
        await call.message.edit_text(text, reply_markup=get_admin_back_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "adm_view:users")
async def cb_admin_users(call: CallbackQuery):
    await call.answer()
    async with async_session_maker() as session:
        s = await AdminService.get_analytics_summary(session)
        text = (
            "👥 <b>Структура пользователей и аудитории:</b>\n\n"
            f"👤 <b>Реальные живые пользователи ({s['real_users']}):</b>\n"
            f"• 👨 Парней: <b>{s['real_male']}</b>\n"
            f"• 👩 Девушек: <b>{s['real_female']}</b>\n"
            f"• 👥 Пар: <b>{s['real_couple']}</b>\n\n"
            f"🤖 <b>Виртуальные профили ({s['fake_users']}):</b>\n"
            f"• 👨 Мужчин: <b>{s['fake_male']}</b>\n"
            f"• 👩 Женщин: <b>{s['fake_female']}</b>\n"
            f"• 👥 Пар: <b>{s['fake_couple']}</b>\n\n"
            "<i>Реальные пользователи всегда видят друг друга первыми. Виртуальные анкеты служат для наполнения базы.</i>"
        )
        await call.message.edit_text(text, reply_markup=get_admin_back_keyboard(), parse_mode="HTML")

@router.callback_query(F.data.startswith("adm_toggle_pass:"))
async def cb_admin_toggle_password(call: CallbackQuery):
    new_val = call.data.split(":")[1]
    async with async_session_maker() as session:
        await AdminService.set_setting(session, "access_password_enabled", new_val)
        status = "включена" if new_val == "1" else "отключена"
        await call.answer(f"Защита паролем {status}!", show_alert=True)
        await render_main_admin_menu(session, call.message, is_edit=True)

@router.callback_query(F.data == "adm_act:set_pass")
async def cb_admin_set_password_prompt(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(AdminSettingsStates.new_access_password)
    await call.message.reply(
        "✏️ <b>Установка пароля доступа</b>\n\n"
        "Напишите новый пароль для входа в чат-бот (пользователям нужно будет ввести его для доступа):\n"
        "<i>(Или отправьте /cancel для отмены)</i>",
        parse_mode="HTML"
    )

@router.message(AdminSettingsStates.new_access_password, F.text)
async def process_new_access_password(message: Message, state: FSMContext):
    new_pass = message.text.strip()
    if len(new_pass) < 2 or len(new_pass) > 50:
        await message.answer("⚠️ Пароль должен быть от 2 до 50 символов. Попробуйте еще раз:")
        return

    await state.clear()
    async with async_session_maker() as session:
        await AdminService.set_setting(session, "access_password", new_pass)
        await AdminService.set_setting(session, "access_password_enabled", "1")
        await message.answer(
            f"✅ <b>Пароль доступа установлен:</b> <code>{html.escape(new_pass)}</code>\n\n"
            "Режим доступа по паролю автоматически <b>ВКЛЮЧЕН</b>.",
            parse_mode="HTML"
        )
        await render_main_admin_menu(session, message, is_edit=False)

@router.callback_query(F.data == "adm_view:bots")
async def cb_admin_bots_menu(call: CallbackQuery):
    await call.answer()
    async with async_session_maker() as session:
        s = await AdminService.get_analytics_summary(session)
        text = (
            "🤖 <b>Управление виртуальными анкетами:</b>\n\n"
            f"В базе сейчас: <b>{s['fake_users']} виртуальных анкет</b>\n"
            f"• 👨 Мужчин: {s['fake_male']}\n"
            f"• 👩 Женщин: {s['fake_female']}\n"
            f"• 👥 Пар: {s['fake_couple']}\n\n"
            "Все анкеты имеют реалистичные города, возрасты, уникальные тексты «О себе» и картинки из каталога.\n"
            "При поиске реальные люди всегда показываются в первую очередь."
        )
        await call.message.edit_text(text, reply_markup=get_bots_management_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "adm_bots:seed")
async def cb_admin_bots_seed(call: CallbackQuery):
    await call.answer("Генерируем анкеты...")
    async with async_session_maker() as session:
        res = await SeedService.seed_fake_users(session, count_per_type=100)
        await call.message.answer(f"✅ Добавлено анкет: 👨 {res['male']}, 👩 {res['female']}, 👥 {res['couple']}!")
        await render_main_admin_menu(session, call.message, is_edit=False)

@router.callback_query(F.data == "adm_bots:clear")
async def cb_admin_bots_clear(call: CallbackQuery):
    await call.answer("Удаляем...")
    async with async_session_maker() as session:
        deleted = await SeedService.clear_fake_users(session)
        await call.message.answer(f"🗑 Удалено {deleted} виртуальных анкет.")
        await render_main_admin_menu(session, call.message, is_edit=False)

@router.callback_query(F.data == "adm_act:close")
async def cb_admin_close(call: CallbackQuery):
    await call.answer("Панель закрыта")
    try:
        await call.message.delete()
    except Exception:
        pass
