$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# Check if already running
$existing = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*run.py*" -and $_.Name -like "*python*" }
if ($existing) {
    Write-Host "Pure Bot is already running (PID: $($existing.ProcessId))."
    exit 0
}

$cmd = "cmd.exe /c `"cd /d `"`"$scriptDir`"`" && .venv\Scripts\python.exe run.py`""
$res = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmd }
if ($res.ReturnValue -eq 0) {
    Write-Host "Pure Bot started successfully as an independent detached service (PID: $($res.ProcessId))."
} else {
    Write-Host "Failed to start bot. Return code: $($res.ReturnValue)"
}
