import asyncio
import sys
from aiogram import Bot
from aiogram.types import InputProfilePhotoStatic, FSInputFile
from bot.config import settings

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

async def main():
    print("Setting bot profile photo...")
    bot = Bot(token=settings.BOT_TOKEN)
    try:
        photo = InputProfilePhotoStatic(photo=FSInputFile("assets/logo.jpg"))
        res = await bot.set_my_profile_photo(photo=photo)
        print("Successfully set bot profile photo! Result:", res)
    except Exception as e:
        print("API response:", e)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
