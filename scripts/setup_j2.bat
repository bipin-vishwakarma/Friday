@echo off
echo ========================================================
echo   FRIDAY 2.0 // SAMSUNG GALAXY J2 NATIVE DESK HUD
echo ========================================================

REM Check if ADB is installed and device connected
adb devices > temp_devices.txt
findstr /C:"device" temp_devices.txt > nul
if %errorlevel% neq 0 (
    echo [!] No ADB device found. Please plug in your Samsung J2 with USB Debugging enabled.
    del temp_devices.txt
    exit /b 1
)
del temp_devices.txt

echo [*] Establishing zero-latency reverse port forward (5173 & 8000)...
adb reverse tcp:5173 tcp:5173
adb reverse tcp:8000 tcp:8000

echo [*] Keeping display awake while connected...
adb shell svc power stayon true

echo [*] Waking up and unlocking screen...
adb shell input keyevent 224
adb shell input keyevent 82

echo [*] Launching Native Friday HUD App (Fullscreen Kiosk)...
adb shell am start -n com.friday.hud/.MainActivity

echo.
echo [OK] Friday Native Desk HUD is active on your Samsung J2!
echo ========================================================
