@echo off
chcp 65001 >nul
title Pure Dating Bot - GitHub Push
echo ======================================================================
echo   Загрузка проекта Pure Dating Bot в репозиторий GitHub
echo   Аккаунт: https://github.com/unuresuc771-web
echo   Репозиторий: https://github.com/unuresuc771-web/pure-dating-bot
echo ======================================================================
echo.
echo Убедитесь, что репозиторий 'pure-dating-bot' создан на https://github.com/new
echo.
"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd\git.exe" push -u origin main
echo.
if %errorlevel% equ 0 (
    echo [УСПЕХ] Все файлы успешно загружены на GitHub!
    echo Ссылка: https://github.com/unuresuc771-web/pure-dating-bot
) else (
    echo [ОШИБКА] Не удалось отправить. Проверьте авторизацию в браузере или токен.
)
echo.
pause
