@echo off
chcp 65001 > nul
echo Stopping Pure Match Bot...
powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*run.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host 'Stopped PID:' $_.ProcessId }"
echo Pure Match Bot stopped.
pause
