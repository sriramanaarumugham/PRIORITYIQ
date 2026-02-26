@echo off
echo Adding firewall rule for Flask port 5000...
netsh advfirewall firewall add rule name="Flask Port 5000" dir=in action=allow protocol=TCP localport=5000
echo Done! Now restart Flask and access from mobile: http://172.20.10.3:5000
pause
