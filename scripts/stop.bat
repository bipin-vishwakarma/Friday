@echo off
echo ========================================================
echo                 FRIDAY 2.0 // SHUTDOWN
echo ========================================================

echo [*] Terminating Python backend processes...
taskkill /F /FI "WINDOWTITLE eq Friday Backend*" > nul 2>&1
wmic process where "commandline like '%%backend\\run.py%%'" delete > nul 2>&1

echo [*] Terminating HUD Vite processes...
taskkill /F /FI "WINDOWTITLE eq Friday HUD*" > nul 2>&1

echo [OK] Friday 2.0 services stopped cleanly.
echo ========================================================
