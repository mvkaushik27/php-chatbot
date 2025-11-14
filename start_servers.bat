@echo off
echo.
echo ====================================
echo   Nalanda Library Chatbot Widget
echo ====================================
echo.

cd /d "%~dp0"

echo Starting Python Backend (port 8000)...
start "Python Backend" cmd /k "cd backend && python api_server.py"

timeout /t 3 /nobreak >nul

echo Starting PHP Frontend (port 8080)...
start "PHP Frontend" cmd /k "cd frontend && php -S localhost:8080"

timeout /t 3 /nobreak >nul

echo.
echo ====================================
echo   Servers Started!
echo ====================================
echo   Backend:  http://localhost:8000
echo   Widget:   http://localhost:8080/widget.html
echo   Admin:    http://localhost:8080/admin_enhanced.php
echo   API Docs: http://localhost:8000/docs
echo ====================================
echo.
echo Opening widget in browser...
timeout /t 2 /nobreak >nul
start http://localhost:8080/widget.html

echo.
echo Servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
pause
