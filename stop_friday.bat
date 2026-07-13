@echo off
echo Stopping FRIDAY AI...

set "BASE=%~dp0"

:: Stop processes by PID file, matching the launchers' PID-tracking.
:: Falls back to taskkill only if no PID files exist (legacy launches).

set /A BACKEND_PID=0
set /A FRONTEND_PID=0

if exist "%BASE%backend.pid" (
    set /p BACKEND_PID=<"%BASE%backend.pid"
    del "%BASE%backend.pid" >nul 2>&1
)
if exist "%BASE%frontend.pid" (
    set /p FRONTEND_PID=<"%BASE%frontend.pid"
    del "%BASE%frontend.pid" >nul 2>&1
)

if %BACKEND_PID% GTR 0 (
    echo Stopping backend (PID %BACKEND_PID%) ...
    taskkill /F /PID %BACKEND_PID% /T >nul 2>&1
)
if %FRONTEND_PID% GTR 0 (
    echo Stopping frontend (PID %FRONTEND_PID%) ...
    taskkill /F /PID %FRONTEND_PID% /T >nul 2>&1
)

:: Fallback: if frontend was started indirectly (npm spawns node), make sure
:: its child node processes attached to the frontend PID are also gone.
if %FRONTEND_PID% GTR 0 if %BACKEND_PID% GTR 0 goto done

:: Legacy fallback when no PID files were found: only nuke the known Friday
:: processes if launched the old way, instead of EVERY python/node on the box.
echo (No PID files found - killing Friday uvicorn / next dev processes only)
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%P /T >nul 2>&1
)
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":3000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%P /T >nul 2>&1
)

:done
echo FRIDAY stopped.
pause
