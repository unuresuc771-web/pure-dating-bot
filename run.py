import sys
import asyncio
import logging

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.database.db import init_db
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.handlers import get_main_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8", mode="a")
    ]
)
logger = logging.getLogger("Pure_Bot")

async def main():
    logger.info("Initializing Pure Telegram Dating Bot...")

    # Проверка наличия токена
    if not settings.BOT_TOKEN or "example" in settings.BOT_TOKEN or settings.BOT_TOKEN.strip() == "":
        logger.error(
            "\n" + "=" * 60 + "\n"
            "❌ ОШИБКА: BOT_TOKEN не задан или содержит шаблонное значение!\n"
            "Пожалуйста, откройте файл .env и укажите ваш реальный токен бота,\n"
            "полученный в Telegram у @BotFather.\n"
            "Пример строки в .env:\n"
            "BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ\n"
            + "=" * 60
        )
        return

    # Инициализация базы данных
    logger.info("Initializing database tables...")
    await init_db()
    logger.info("Database initialized successfully.")

    # Инициализация бота и диспетчера
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Регистрация middleware
    throttling_middleware = ThrottlingMiddleware(rate_limit=settings.THROTTLE_RATE_LIMIT)
    dp.message.middleware(throttling_middleware)
    dp.callback_query.middleware(throttling_middleware)

    from bot.middlewares.access_gate import AccessGateMiddleware
    access_gate_middleware = AccessGateMiddleware()
    dp.message.middleware(access_gate_middleware)
    dp.callback_query.middleware(access_gate_middleware)

    # Подключение роутеров
    main_router = get_main_router()
    dp.include_router(main_router)

    logger.info("Starting bot polling...")
    try:
        await bot.delete_webhook(drop_pending_updates=False)

        # Поддержка облачных PaaS (Render, Koyeb, Railway) при наличии переменной PORT
        import os
        port_env = os.getenv("PORT")
        if port_env:
            try:
                from aiohttp import web
                async def health_handler(request):
                    return web.Response(text="Pure Match Bot is running 24/7!", status=200)
                app = web.Application()
                app.router.add_get("/", health_handler)
                app.router.add_get("/health", health_handler)
                runner = web.AppRunner(app)
                await runner.setup()
                site = web.TCPSite(runner, "0.0.0.0", int(port_env))
                await site.start()
                logger.info(f"Cloud health-check server started on 0.0.0.0:{port_env}")
            except Exception as e:
                logger.warning(f"Could not start health-check server: {e}")

        # Отправка уведомления админам асинхронно без блокировки старта
        async def notify_admins():
            for admin_id in settings.admin_list:
                try:
                    await bot.send_message(admin_id, "🚀 <b>Pure Dating Bot успешно запущен!</b>")
                except Exception:
                    pass
        asyncio.create_task(notify_admins())

        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot process interrupted.")
