@echo off
REM ========================================
REM Nalanda Library Chatbot - Local Testing Startup
REM PHP Frontend + Python Backend
REM ========================================

echo.
echo ====================================
echo   Nalanda Library Chatbot - Local Testing
echo   PHP Frontend + Python Backend
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.9+ from https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Check if PHP is installed
php --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PHP not found!
    echo Please install PHP from https://www.php.net/downloads
    echo.
    pause
    exit /b 1
)

echo [INFO] Python and PHP detected successfully
echo.

REM Check if required files exist in backend
if not exist "backend\nandu_brain.py" (
    echo [ERROR] Missing backend\nandu_brain.py
    echo.
    echo Please copy these files from your main project to backend\:
    echo   - nandu_brain.py
    echo   - formatters.py
    echo   - catalogue.db
    echo   - general_queries.json
    echo   - general_queries_index.faiss
    echo   - general_queries_mapping.pkl
    echo   - catalogue_index.faiss
    echo   - catalogue_mapping.pkl
    echo   - models\ folder
    echo.
    pause
    exit /b 1
)

echo [1/5] Checking and updating Python dependencies...
cd backend
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing FastAPI and dependencies...
    pip install fastapi uvicorn python-dotenv
)

echo [INFO] Upgrading sentence-transformers to latest version...
pip install --upgrade sentence-transformers>=5.1.2

echo [2/5] Starting Python Backend API...
start "Nalanda Python Backend" cmd /k "python api_server.py"
timeout /t 5 >nul

echo [3/5] Starting PHP Built-in Server...
cd ..\frontend
start "Nalanda PHP Frontend" cmd /k "php -S localhost:80"
timeout /t 3 >nul

echo [4/5] Waiting for servers to start...
timeout /t 2 >nul

echo [5/5] Opening Browser...
start http://localhost

echo.
echo ====================================
echo   Servers Started Successfully!
echo ====================================
echo.
echo Python Backend: http://localhost:8000
echo   - API Docs:   http://localhost:8000/docs
echo   - Test Page:  http://localhost:8000/test
echo   - Health:     http://localhost:8000/health
echo.
echo PHP Frontend:   http://localhost
echo   - Main Page:  http://localhost
echo.
echo ====================================
echo.
echo Press any key to STOP all servers...
pause >nul

echo.
echo [INFO] Stopping servers...
taskkill /FI "WINDOWTITLE eq Nalanda Python Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Nalanda PHP Frontend*" /F >nul 2>&1

echo [INFO] Servers stopped.
echo.
pause
