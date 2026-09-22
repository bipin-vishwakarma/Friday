@echo off
setlocal
cd /d "%~dp0\.."
echo ========================================================
echo                 FRIDAY 2.0 // LAUNCHER
echo ========================================================

REM 1. Start Backend in background
echo [*] Starting Friday Backend (FastAPI + Laya Router)...
start "Friday Backend" /min "%~dp0..\.venv\Scripts\python.exe" backend\run.py

REM Wait 2 seconds for backend to bind port 8000
timeout /t 2 /nobreak > nul

REM 2. Start HUD in background
echo [*] Starting Friday Cyber HUD (Vite)...
cd /d "%~dp0..\hud"
start "Friday HUD" /min npm run dev

REM Wait 2 seconds for Vite to bind port 5173
timeout /t 2 /nobreak > nul

REM 3. Setup Samsung J2 Desk Screen via ADB
echo [*] Connecting Samsung J2 Companion Screen...
call "%~dp0setup_j2.bat"

REM 4. Also open HUD in default PC browser
echo [*] Opening Desktop Interface (http://localhost:5173)...
start http://localhost:5173

echo.
echo ========================================================
echo   FRIDAY 2.0 IS RUNNING!
echo   - Desk HUD: http://localhost:5173 (Streaming to J2)
echo   - Backend API: http://localhost:8000
echo   - To stop Friday, run: scripts\stop.bat
echo ========================================================
