from aiogram import Router
from .common import router as common_router
from .start import router as start_router
from .registration import router as registration_router
from .discovery import router as discovery_router
from .profile import router as profile_router
from .chat import router as chat_router
from .admin import router as admin_router

def get_main_router() -> Router:
    main_router = Router(name="main_router")
    main_router.include_router(admin_router)
    main_router.include_router(common_router)
    main_router.include_router(start_router)
    main_router.include_router(registration_router)
    main_router.include_router(discovery_router)
    main_router.include_router(profile_router)
    main_router.include_router(chat_router)
    return main_router
