@echo off
echo === FRIDAY Quick Test ===
cd /d "C:\Users\Lenovo\Desktop\Friday"
python test_friday.py
echo.
echo === API Health Check ===
curl -s http://localhost:8000/health 2>nul || echo Backend not running
pause
