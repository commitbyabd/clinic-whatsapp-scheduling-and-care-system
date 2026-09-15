@echo off
rem Makes the backend start by itself whenever the server boots.
rem Run once, as Administrator. Running it again just updates the task.

%SystemRoot%\System32\whoami.exe /groups | %SystemRoot%\System32\find.exe "S-1-16-12288" > nul || (
    echo Run this as Administrator: right-click it, then Run as administrator.
    exit /b 1
)

set "CWAC_RUN=%~dp0run.cmd"

rem runs as SYSTEM so it starts before anyone logs in, and with no time limit,
rem because a task created the usual way is stopped after 3 days
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; $q = [char]34; $action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument ('/c ' + $q + $env:CWAC_RUN + $q); $trigger = New-ScheduledTaskTrigger -AtStartup; $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries; Register-ScheduledTask -TaskName 'CWAC Backend' -Action $action -Trigger $trigger -Settings $settings -User 'SYSTEM' -RunLevel Highest -Force | Out-Null" || exit /b 1

echo Done. The backend now starts by itself whenever the server boots.
echo To start it now without restarting the server, run: schtasks /run /tn "CWAC Backend"
