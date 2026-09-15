@echo off
rem Stops the backend. Run as Administrator.
rem If you started run.cmd by double-clicking it, close that window instead.

%SystemRoot%\System32\whoami.exe /groups | %SystemRoot%\System32\find.exe "S-1-16-12288" > nul || (
    echo Run this as Administrator: right-click it, then Run as administrator.
    exit /b 1
)

set "running="
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":7222 " ^| findstr "LISTENING"') do set "running=%%p"

rem end the task first, or its restart loop brings the backend straight back
schtasks /end /tn "CWAC Backend" > nul 2>&1
if defined running taskkill /pid %running% /f > nul 2>&1

if defined running (echo Backend stopped.) else (echo Backend was not running.)
