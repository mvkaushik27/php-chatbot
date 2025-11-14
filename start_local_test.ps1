# ====================================
#   Nalanda Library Chatbot - Local Testing
#   PHP Frontend + Python Backend
# ====================================

Write-Host "`n====================================" -ForegroundColor Cyan
Write-Host "  Nalanda Library Chatbot - Local Testing" -ForegroundColor Cyan
Write-Host "  PHP Frontend + Python Backend" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

# Refresh PATH environment
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Check Python
Write-Host "`n[1/5] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found!" -ForegroundColor Red
    Write-Host "  Please install Python from https://www.python.org/" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check PHP
Write-Host "`n[2/5] Checking PHP..." -ForegroundColor Yellow
try {
    $phpVersion = php --version 2>&1 | Select-Object -First 1
    Write-Host "  ✓ Found: $phpVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ PHP not found!" -ForegroundColor Red
    Write-Host "  Please install PHP from https://www.php.net/" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check backend files
Write-Host "`n[3/5] Checking backend files..." -ForegroundColor Yellow
$requiredFiles = @(
    "backend\api_server.py",
    "backend\nandu_brain.py",
    "backend\formatters.py",
    "backend\catalogue.db"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✓ $file" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Missing: $file" -ForegroundColor Red
        Write-Host "`nPlease run copy_files.ps1 first!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Install Python dependencies
Write-Host "`n[4/5] Installing Python dependencies..." -ForegroundColor Yellow
Set-Location backend
try {
    python -m pip install -q fastapi uvicorn python-dotenv pydantic 2>&1 | Out-Null
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Warning: Could not install some dependencies" -ForegroundColor Yellow
}
Set-Location ..

# Start servers
Write-Host "`n[5/5] Starting servers..." -ForegroundColor Yellow

# Start Python backend in new window
Write-Host "  → Starting Python backend (port 8000)..." -ForegroundColor Cyan
$pythonProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; python api_server.py" -PassThru -WindowStyle Normal

Start-Sleep -Seconds 3

# Start PHP frontend in new window  
Write-Host "  → Starting PHP frontend (port 80)..." -ForegroundColor Cyan
$phpProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; php -S localhost:80" -PassThru -WindowStyle Normal

Start-Sleep -Seconds 2

# Open browser
Write-Host "`n✓ Servers started successfully!" -ForegroundColor Green
Write-Host "`n====================================" -ForegroundColor Cyan
Write-Host "  Access the application at:" -ForegroundColor White
Write-Host "  → Frontend: http://localhost" -ForegroundColor Yellow
Write-Host "  → Backend API: http://localhost:8000" -ForegroundColor Yellow
Write-Host "  → API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "  → Test Page: http://localhost:8000/test" -ForegroundColor Yellow
Write-Host "====================================" -ForegroundColor Cyan

Write-Host "`nOpening browser..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
Start-Process "http://localhost"

Write-Host "`n[INFO] Servers are running in separate windows" -ForegroundColor White
Write-Host "[INFO] Close those windows to stop the servers" -ForegroundColor White
Write-Host "`nPress any key to exit this launcher..." -ForegroundColor Gray
Read-Host
