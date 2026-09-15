@echo off
rem Starts the CWAC backend on port 7222 and restarts it if it ever stops.
rem The "CWAC Backend" startup task runs this. Double-clicking it works too.

rem .env is read from the working directory, so always start from this folder
cd /d "%~dp0"
if not exist logs mkdir logs

if not exist ".venv\Scripts\python.exe" (
    echo No .venv found next to run.cmd. Create it and install requirements.txt first.
    echo [%date% %time%] no .venv found, not starting >> logs\backend.log
    exit /b 1
)

echo Backend running on port 7222. Output goes to %cd%\logs\backend.log

:start
echo [%date% %time%] starting backend >> logs\backend.log
".venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 7222 --workers 1 >> logs\backend.log 2>&1

rem right after boot the network may not be ready and startup fails on the
rem database check, so wait and try again rather than staying down
echo [%date% %time%] backend stopped with code %errorlevel%, restarting in 10 seconds >> logs\backend.log
%SystemRoot%\System32\ping.exe -n 11 127.0.0.1 > nul
goto start
