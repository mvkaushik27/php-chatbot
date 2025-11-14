# Nalanda Chatbot - Automated Data Sync Script
# Syncs data from main project to PHP integration and rebuilds FAISS indices

Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  Nalanda Chatbot - PHP Integration Data Update Script  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Configuration
$mainProject = "C:\Users\Admin\Videos\Nalanda_Chatbot"
$phpBackend = "C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend"

# Check if directories exist
if (-not (Test-Path $mainProject)) {
    Write-Host "❌ Main project not found at: $mainProject" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $phpBackend)) {
    Write-Host "❌ PHP backend not found at: $phpBackend" -ForegroundColor Red
    exit 1
}

# Create backup timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "$phpBackend\backups\$timestamp"

# Step 0: Create backup
Write-Host "📦 Step 0: Creating backup..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

if (Test-Path "$phpBackend\general_queries.json") {
    Copy-Item "$phpBackend\general_queries.json" -Destination "$backupDir\general_queries.json" -Force
    Write-Host "   ✅ Backed up general_queries.json" -ForegroundColor Green
}

if (Test-Path "$phpBackend\catalogue.db") {
    Copy-Item "$phpBackend\catalogue.db" -Destination "$backupDir\catalogue.db" -Force
    Write-Host "   ✅ Backed up catalogue.db" -ForegroundColor Green
}

# Step 1: Copy data files
Write-Host "`n📋 Step 1: Copying data files from main project..." -ForegroundColor Yellow

if (Test-Path "$mainProject\general_queries.json") {
    Copy-Item "$mainProject\general_queries.json" -Destination "$phpBackend\general_queries.json" -Force
    Write-Host "   ✅ Copied general_queries.json" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  general_queries.json not found in main project" -ForegroundColor Yellow
}

if (Test-Path "$mainProject\catalogue.db") {
    Copy-Item "$mainProject\catalogue.db" -Destination "$phpBackend\catalogue.db" -Force
    $sizeKB = [math]::Round((Get-Item "$phpBackend\catalogue.db").Length / 1KB, 2)
    Write-Host "   ✅ Copied catalogue.db ($sizeKB KB)" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  catalogue.db not found in main project" -ForegroundColor Yellow
}

# Step 2: Rebuild general queries FAISS index
Write-Host "`n🔧 Step 2: Rebuilding general queries FAISS index..." -ForegroundColor Yellow
Set-Location $phpBackend

try {
    $output = python build_general_queries_index.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ General queries index rebuilt successfully" -ForegroundColor Green
        if ($output -match "Loaded (\d+)") {
            Write-Host "      Indexed $($matches[1]) queries" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⚠️  Warning: Index rebuild may have issues" -ForegroundColor Yellow
        Write-Host "      $output" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Failed to rebuild general queries index: $_" -ForegroundColor Red
}

# Step 3: Rebuild catalogue FAISS index
Write-Host "`n🔧 Step 3: Rebuilding catalogue FAISS index..." -ForegroundColor Yellow

# Export database to CSV first
try {
    $output = python export_catalogue_to_csv.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Exported catalogue.db to CSV" -ForegroundColor Green
        if ($output -match "(\d+) rows") {
            Write-Host "      Exported $($matches[1]) book records" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⚠️  Warning: CSV export may have issues" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ Failed to export catalogue: $_" -ForegroundColor Red
}

# Build FAISS index from CSV
try {
    Write-Host "   🔄 Building FAISS index (this may take 2-5 minutes)..." -ForegroundColor Gray
    $output = python catalogue_indexer.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Catalogue FAISS index rebuilt successfully" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Warning: Index rebuild may have issues" -ForegroundColor Yellow
        Write-Host "      $output" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Failed to rebuild catalogue index: $_" -ForegroundColor Red
}

# Step 4: Verify indices
Write-Host "`n🔍 Step 4: Verifying FAISS indices..." -ForegroundColor Yellow

$indices = @{
    "general_queries_index.faiss" = "General Queries"
    "catalogue_index.faiss" = "Catalogue"
}

foreach ($file in $indices.Keys) {
    $filePath = "$phpBackend\$file"
    if (Test-Path $filePath) {
        $sizeKB = [math]::Round((Get-Item $filePath).Length / 1KB, 2)
        $modified = (Get-Item $filePath).LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        Write-Host "   ✅ $($indices[$file]): $sizeKB KB (updated: $modified)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $($indices[$file]): Missing!" -ForegroundColor Red
    }
}

# Summary
Write-Host "`n╔══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    Update Summary                        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host "`n✅ Data sync completed!" -ForegroundColor Green
Write-Host "   📂 Backup location: $backupDir" -ForegroundColor Gray
Write-Host "   🔄 PHP Integration is now up to date with main project" -ForegroundColor Gray

Write-Host "`n📝 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Restart API server: python api_server.py" -ForegroundColor White
Write-Host "   2. Test chatbot: http://localhost:8080" -ForegroundColor White
Write-Host "   3. Verify in admin panel: http://localhost:8080/admin_enhanced.php" -ForegroundColor White

Write-Host "`n💡 Tip: Run this script whenever you update data in the main project!" -ForegroundColor Cyan
Write-Host ""
