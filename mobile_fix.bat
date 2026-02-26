@echo off
echo ========================================
echo PriorityIQ - Mobile Access Troubleshooter
echo ========================================
echo.

echo Step 1: Checking your IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%
echo Your IP: %IP%
echo.

echo Step 2: Testing if Flask is running...
netstat -an | findstr :5000 >nul
if %errorlevel%==0 (
    echo [OK] Flask is running on port 5000
) else (
    echo [ERROR] Flask is NOT running!
    echo Please start Flask first: python app.py
    pause
    exit
)
echo.

echo Step 3: Adding firewall rules...
netsh advfirewall firewall delete rule name="Flask Port 5000" >nul 2>&1
netsh advfirewall firewall add rule name="Flask Port 5000" dir=in action=allow protocol=TCP localport=5000 >nul
echo [OK] Firewall rule added
echo.

echo Step 4: Checking network profile...
powershell -Command "Get-NetConnectionProfile | Select-Object Name, NetworkCategory"
echo.
echo If NetworkCategory is 'Public', change to 'Private':
echo Settings ^> Network ^& Internet ^> WiFi ^> [Your Network] ^> Network profile: Private
echo.

echo ========================================
echo MOBILE ACCESS INSTRUCTIONS:
echo ========================================
echo 1. Make sure mobile and PC are on SAME WiFi
echo 2. On mobile Chrome, open: http://%IP%:5000
echo 3. If still not working, try:
echo    - Restart Flask
echo    - Restart WiFi router
echo    - Disable VPN on mobile
echo    - Check PC firewall settings
echo ========================================
echo.
pause
