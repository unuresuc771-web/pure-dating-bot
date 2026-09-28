import os
import json
import logging
from typing import Optional
from aiogram import Bot
from aiogram.types import Message, FSInputFile

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_FILE_PATH = os.path.join(BASE_DIR, "assets", "avatar_cache.json")

def to_normalized_key(path: str) -> str:
    """Нормализует путь к виду assets/avatars/gender/file.jpg для унифицированного кэша."""
    if not path:
        return ""
    clean = path.replace("\\", "/")
    if "assets/" in clean:
        return "assets/" + clean.split("assets/", 1)[1]
    return clean

def resolve_existing_image(path: str) -> Optional[str]:
    """Находит реальный физический файл на диске, независимо от ОС и типа пути."""
    if not path:
        return None
    # 1. Прямой путь
    if os.path.exists(path) and os.path.isfile(path):
        return path
    # 2. Относительно корня проекта
    rel_key = to_normalized_key(path)
    proj_path = os.path.join(BASE_DIR, *rel_key.split("/"))
    if os.path.exists(proj_path) and os.path.isfile(proj_path):
        return proj_path
    # 3. В текущей рабочей директории
    if os.path.exists(rel_key) and os.path.isfile(rel_key):
        return os.path.abspath(rel_key)
    # 4. Fallback на первый существующий аватар соответствующего пола (НИКОГДА не логотип чата!)
    for gender in ["male", "female", "couple"]:
        if gender in rel_key:
            gender_dir = os.path.join(BASE_DIR, "assets", "avatars", gender)
            if os.path.exists(gender_dir):
                files = [os.path.join(gender_dir, f) for f in os.listdir(gender_dir) if f.endswith(".jpg")]
                if files:
                    return sorted(files)[0]
    return None

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
                    raw = json.load(f)
                    cls._cache = {to_normalized_key(k): v for k, v in raw.items() if isinstance(v, str)}
            except Exception as e:
                logger.warning(f"Failed to load avatar cache from {CACHE_FILE_PATH}: {e}")
                cls._cache = {}
        cls._loaded = True

    @classmethod
    def _save(cls):
        try:
            os.makedirs(os.path.dirname(CACHE_FILE_PATH), exist_ok=True)
            clean_cache = {str(k): str(v) for k, v in cls._cache.items() if isinstance(v, str)}
            with open(CACHE_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(clean_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save avatar cache to {CACHE_FILE_PATH}: {e}")

    @classmethod
    def get_file_id(cls, local_path: str) -> Optional[str]:
        cls._load()
        key = to_normalized_key(local_path)
        return cls._cache.get(key)

    @classmethod
    def set_file_id(cls, local_path: str, file_id: str):
        cls._load()
        key = to_normalized_key(local_path)
        cls._cache[key] = file_id
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
        Отправляет фото анкеты:
        - Если пользователь загрузил личное фото: отправляет по telegram file_id.
        - Если образ из каталога/виртуал: ищет в кэше file_id по нормализованному ключу.
        - При отсутствии в кэше: надежно находит файл на диске, загружает и кэширует file_id.
        - При любых сбоях гарантирует отправку фотографии.
        """
        if is_custom_photo:
            try:
                return await bot.send_photo(
                    chat_id=chat_id,
                    photo=avatar_path,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Failed to send custom photo {avatar_path}: {e}")

        # 1. Попытка отправить из кэша Telegram file_id
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
                logger.warning(f"Sending cached file_id failed, re-uploading file: {e}")

        # 2. Поиск физического файла на диске
        file_on_disk = resolve_existing_image(avatar_path)
        if file_on_disk:
            try:
                sent = await bot.send_photo(
                    chat_id=chat_id,
                    photo=FSInputFile(file_on_disk),
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
                if sent.photo:
                    cls.set_file_id(avatar_path, sent.photo[-1].file_id)
                return sent
            except Exception as e:
                logger.error(f"Failed to upload photo from {file_on_disk}: {e}")

        # 3. Аварийный fallback: отправка текста только если отправка фото категорически невозможна
        return await bot.send_message(
            chat_id=chat_id,
            text=caption,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
