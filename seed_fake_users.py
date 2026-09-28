import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.database.db import init_db, async_session_maker
from bot.services.seed_service import SeedService

async def main():
    print("Initializing database...")
    await init_db()
    print("Generating 300 realistic virtual profiles (100 men, 100 women, 100 couples)...")
    async with async_session_maker() as session:
        counts = await SeedService.seed_fake_users(session, count_per_type=100)
        print(f"Done! Created profiles: {counts}")

if __name__ == "__main__":
    asyncio.run(main())
