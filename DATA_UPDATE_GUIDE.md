# Nalanda Chatbot - Data Update Guide for PHP Integration

## 🎯 Quick Reference: How to Update Data

### Method 1: Using Admin Panel (Recommended) ⭐

#### **Access Admin Panel:**
```
URL: http://localhost:8080/admin_enhanced.php?admin=1
Login: Use your admin credentials
```

#### **Update General Queries:**
1. Click **"📝 General Queries"** tab
2. Edit directly in the table OR
3. Click **"📄 File Manager"** → Upload new `general_queries.json`
4. Go to **"🔍 FAISS Indices"** tab → Click **"🔄 Rebuild"** for General Queries

#### **Update Catalogue:**
1. Click **"🔍 FAISS Indices"** tab
2. Upload new `catalogue.json` (if you have it) OR update the database directly
3. Click **"🔄 Rebuild"** for Catalogue Index
4. Wait for success message

---

### Method 2: Manual File Update (Advanced)

#### **A) Update General Queries JSON**

**Step 1: Edit the JSON file**
```powershell
# Open in editor
notepad "C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend\general_queries.json"

# OR copy from main project
Copy-Item "C:\Users\Admin\Videos\Nalanda_Chatbot\general_queries.json" `
          -Destination "C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend\general_queries.json"
```

**Step 2: Rebuild FAISS Index**
```powershell
cd "C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend"
python build_general_queries_index.py
```

**Expected Output:**
```
Loading general queries...
Loaded 45 queries
Generating embeddings...
Building FAISS index...
Saved FAISS index and mapping
Indexing completed successfully!
```

---

#### **B) Update Catalogue Database**

**Option 1: Copy Database from Main Project**
```powershell
Copy-Item "C:\Users\Admin\Videos\Nalanda_Chatbot\catalogue.db" `
          -Destination "C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend\catalogue.db" `
          -Force
```

**Option 2: Import CSV Data**
```powershell
# If you have a CSV file with updated book data
cd "C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend"

# Import CSV to SQLite (using Python)
python -c "
import pandas as pd
import sqlite3

# Read CSV
df = pd.read_csv('catalogue.csv')

# Write to database
conn = sqlite3.connect('catalogue.db')
df.to_sql('catalogue', conn, if_exists='replace', index=False)
conn.close()
print('✅ Catalogue database updated!')
"
```

**Step 2: Export to CSV and Rebuild FAISS Index**
```powershell
cd "C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend"

# Export database to CSV
python export_catalogue_to_csv.py

# Rebuild FAISS index
python catalogue_indexer.py
```

**Expected Output:**
```
Found tables: ['catalogue']
Using table: catalogue
Successfully exported 25196 rows to catalogue.csv

Loading catalogue...
Initializing sentence transformer...
Processing catalogue entries...
Generating embeddings...
Building FAISS index...
Saving index and metadata...
Catalogue indexing completed!
```

---

### Method 3: Sync from Main Project (Quick Sync)

If you want to keep PHP integration in sync with the main Nalanda_Chatbot project:

```powershell
# Create a sync script
$mainProject = "C:\Users\Admin\Videos\Nalanda_Chatbot"
$phpBackend = "C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend"

# Copy general queries
Copy-Item "$mainProject\general_queries.json" -Destination "$phpBackend\general_queries.json" -Force
Write-Host "✅ Copied general_queries.json" -ForegroundColor Green

# Copy catalogue database
Copy-Item "$mainProject\catalogue.db" -Destination "$phpBackend\catalogue.db" -Force
Write-Host "✅ Copied catalogue.db" -ForegroundColor Green

# Copy FAISS indices (optional - or rebuild them)
Copy-Item "$mainProject\general_queries_index.faiss" -Destination "$phpBackend\general_queries_index.faiss" -Force
Copy-Item "$mainProject\general_queries_mapping.pkl" -Destination "$phpBackend\general_queries_mapping.pkl" -Force
Write-Host "✅ Copied general queries FAISS index" -ForegroundColor Green

Copy-Item "$mainProject\catalogue_index.faiss" -Destination "$phpBackend\catalogue_index.faiss" -Force
Copy-Item "$mainProject\catalogue_mapping.pkl" -Destination "$phpBackend\catalogue_mapping.pkl" -Force
Write-Host "✅ Copied catalogue FAISS index" -ForegroundColor Green

Write-Host "`n🎉 Sync completed! PHP integration is now up to date." -ForegroundColor Cyan
```

**Save this as:** `sync_data.ps1` and run it whenever you update the main project.

---

## 📂 File Locations Reference

### Main Nalanda_Chatbot Project:
```
C:\Users\Admin\Videos\Nalanda_Chatbot\
├── general_queries.json              ← Source file
├── catalogue.db                       ← Source database
├── general_queries_index.faiss        ← Generated index
├── general_queries_mapping.pkl        ← Generated mapping
├── catalogue_index.faiss              ← Generated index
└── catalogue_mapping.pkl              ← Generated mapping
```

### PHP Integration Backend:
```
C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend\
├── general_queries.json              ← Target file
├── catalogue.db                       ← Target database
├── catalogue.csv                      ← Temporary (auto-generated)
├── general_queries_index.faiss        ← Target index
├── general_queries_mapping.pkl        ← Target mapping
├── catalogue_index.faiss              ← Target index
├── catalogue_mapping.pkl              ← Target mapping
├── build_general_queries_index.py     ← Rebuild script
├── catalogue_indexer.py               ← Rebuild script
└── export_catalogue_to_csv.py         ← Export script
```

---

## 🔄 Automatic Update Script

Create this PowerShell script to automate everything:

```powershell
# update_php_integration.ps1
Write-Host "🔄 Starting PHP Integration Update..." -ForegroundColor Cyan

$mainProject = "C:\Users\Admin\Videos\Nalanda_Chatbot"
$phpBackend = "C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend"

# 1. Copy data files
Write-Host "`n📋 Step 1: Copying data files..." -ForegroundColor Yellow
Copy-Item "$mainProject\general_queries.json" -Destination "$phpBackend\general_queries.json" -Force
Copy-Item "$mainProject\catalogue.db" -Destination "$phpBackend\catalogue.db" -Force
Write-Host "✅ Data files copied" -ForegroundColor Green

# 2. Rebuild general queries index
Write-Host "`n🔧 Step 2: Rebuilding general queries FAISS index..." -ForegroundColor Yellow
Set-Location $phpBackend
python build_general_queries_index.py
Write-Host "✅ General queries index rebuilt" -ForegroundColor Green

# 3. Rebuild catalogue index
Write-Host "`n🔧 Step 3: Rebuilding catalogue FAISS index..." -ForegroundColor Yellow
python export_catalogue_to_csv.py
python catalogue_indexer.py
Write-Host "✅ Catalogue index rebuilt" -ForegroundColor Green

Write-Host "`n🎉 Update completed successfully!" -ForegroundColor Cyan
Write-Host "   You can now restart your PHP server if needed." -ForegroundColor Gray
```

**Usage:**
```powershell
.\update_php_integration.ps1
```

---

## ⚠️ Important Notes

1. **Always backup before updating:**
   ```powershell
   # Backup current files
   $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
   Copy-Item "$phpBackend\general_queries.json" -Destination "$phpBackend\general_queries_backup_$timestamp.json"
   Copy-Item "$phpBackend\catalogue.db" -Destination "$phpBackend\catalogue_backup_$timestamp.db"
   ```

2. **Index rebuild is required after data updates:**
   - Updating JSON/database alone is not enough
   - FAISS indices must be rebuilt for search to work
   - Admin panel does this automatically

3. **Restart API server after updates:**
   ```powershell
   # Stop current server (Ctrl+C)
   # Then restart
   cd "C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend"
   python api_server.py
   ```

4. **Verify updates:**
   - Test a query in the chatbot
   - Check admin panel FAISS tab for updated timestamps
   - Look for index file size changes

---

## 🧪 Testing After Update

```powershell
# Test general queries index
cd "C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend"
python -c "
from nandu_brain import semantic_search_general_queries
results = semantic_search_general_queries('library hours')
print('✅ General queries working!' if results else '❌ Error')
"

# Test catalogue index
python -c "
from nandu_brain import semantic_search
results = semantic_search('python programming')
print('✅ Catalogue search working!' if results else '❌ Error')
"
```

---

## 🆘 Troubleshooting

### "Index not found" error:
```powershell
# Rebuild both indices
cd "C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend"
python build_general_queries_index.py
python export_catalogue_to_csv.py
python catalogue_indexer.py
```

### "Module not found" error:
```powershell
# Install dependencies
pip install sentence-transformers faiss-cpu pandas numpy
```

### Admin panel upload fails:
- Check file size (< 10 MB)
- Verify JSON format is valid
- Check file permissions
- Look at PHP error logs

---

## 📞 Quick Help

**Admin Panel URL:** http://localhost:8080/admin_enhanced.php?admin=1  
**Backend Location:** C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend\  
**Support:** mahavir@iitrpr.ac.in

---

**Last Updated:** November 2025  
**Version:** 1.0
