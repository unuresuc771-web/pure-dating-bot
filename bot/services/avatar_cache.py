import os
import json
import logging
from typing import Optional
from aiogram import Bot
from aiogram.types import Message, FSInputFile

logger = logging.getLogger(__name__)

CACHE_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "assets",
    "avatar_cache.json"
)

class AvatarCacheService:
    _cache: dict[str, str] = {}
    _loaded: bool = False

    @classmethod
    def _load(cls):
        if cls._loaded:
            return
        if os.path.exists(CACHE_FILE_PATH):
            try:
                with open(CACHE_FILE_PATH, "r", encoding="utf-8") as f:
                    cls._cache = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load avatar cache from {CACHE_FILE_PATH}: {e}")
                cls._cache = {}
        cls._loaded = True

    @classmethod
    def _save(cls):
        try:
            os.makedirs(os.path.dirname(CACHE_FILE_PATH), exist_ok=True)
            with open(CACHE_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(cls._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save avatar cache to {CACHE_FILE_PATH}: {e}")

    @classmethod
    def get_file_id(cls, local_path: str) -> Optional[str]:
        cls._load()
        norm = os.path.normpath(local_path)
        return cls._cache.get(norm)

    @classmethod
    def set_file_id(cls, local_path: str, file_id: str):
        cls._load()
        norm = os.path.normpath(local_path)
        cls._cache[norm] = file_id
        cls._save()

    @classmethod
    async def send_avatar_photo(
        cls,
        bot: Bot,
        chat_id: int,
        avatar_path: str,
        is_custom_photo: bool,
        caption: str,
        reply_markup=None
    ) -> Message:
        """
        Sends an avatar photo with instant response:
        - If custom photo, uses telegram file_id directly.
        - If preset persona avatar, checks telegram file_id cache.
        - Falls back to FSInputFile on cache miss, and caches the returned file_id.
        """
        if is_custom_photo:
            return await bot.send_photo(
                chat_id=chat_id,
                photo=avatar_path,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )

        cached_file_id = cls.get_file_id(avatar_path)
        if cached_file_id:
            try:
                return await bot.send_photo(
                    chat_id=chat_id,
                    photo=cached_file_id,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Sending cached file_id failed, re-uploading {avatar_path}: {e}")

        # Send via FSInputFile and cache result
        if os.path.exists(avatar_path):
            sent = await bot.send_photo(
                chat_id=chat_id,
                photo=FSInputFile(avatar_path),
                caption=caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
            if sent.photo:
                cls.set_file_id(avatar_path, sent.photo[-1].file_id)
            return sent
        else:
            return await bot.send_message(
                chat_id=chat_id,
                text=caption,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
