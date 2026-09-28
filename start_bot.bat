@echo off
chcp 65001 > nul
title Pure Match Bot
echo ====================================================
echo        Pure Telegram Dating Bot (@pure_match_bot)
echo ====================================================
echo.
cd /d "%~dp0"
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe run.py
) else (
    python run.py
)
echo.
echo Бот остановлен. Нажмите любую клавишу для выхода...
pause > nul
