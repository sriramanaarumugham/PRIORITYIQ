@echo off
echo ========================================
echo PriorityIQ - Mobile Access Setup
echo ========================================
echo.

echo Step 1: Adding Firewall Rule...
netsh advfirewall firewall delete rule name="Flask Port 5000" >nul 2>&1
netsh advfirewall firewall add rule name="Flask Port 5000" dir=in action=allow protocol=TCP localport=5000
echo [OK] Firewall rule added
echo.

echo Step 2: Getting your IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%
echo [OK] Your IP: %IP%
echo.

echo Step 3: Starting Flask server...
echo Access from mobile: http://%IP%:5000
echo Press Ctrl+C to stop server
echo.
python app.py
pause
