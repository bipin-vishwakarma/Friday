@echo off
title FRIDAY AI - Master Launcher
echo.
echo  ███████╗██████╗ ██╗██████╗  █████╗ ██╗   ██╗
echo  ██╔════╝██╔══██╗██║██╔══██╗██╔══██╗╚██╗ ██╔╝
echo  █████╗  ██████╔╝██║██║  ██║███████║ ╚████╔╝
echo  ██╔══╝  ██╔══██╗██║██║  ██║██╔══██║  ╚██╔╝
echo  ██║     ██║  ██║██║██████╔╝██║  ██║   ██║
echo  ╚═╝     ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝   ╚═╝
echo.
echo  Your Iron Man AI Desktop Assistant
echo  ======================================
echo.

cd /d "C:\Users\Lenovo\Desktop\Friday"

echo [1/2] Starting Backend API...
start "FRIDAY Backend" cmd /k "python -m uvicorn src.friday.api.main:app --host 127.0.0.1 --port 8000"

echo Waiting 3 seconds for backend to initialize...
timeout /t 3 /nobreak > nul

echo [2/2] Starting Frontend...
start "FRIDAY Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================
echo  FRIDAY is starting up!
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:3000
echo  API Docs: http://localhost:8000/docs
echo ============================================
echo.
echo Opening browser in 5 seconds...
timeout /t 5 /nobreak > nul
start http://localhost:3000

echo.
echo Both windows are running. Close them to stop FRIDAY.
pause
