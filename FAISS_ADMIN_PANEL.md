# FAISS Index Management in Admin Panel

## Overview
The enhanced admin panel now includes a dedicated **FAISS Indices** tab for managing and rebuilding vector search indices used by the chatbot.

## Features Added

### 1. **FAISS Indices Tab**
Located in `admin_enhanced.php`, this new tab provides:

#### Index Status Display
- **Catalogue Index**: Powers book search and recommendations
- **General Queries Index**: Enables FAQ matching and library information retrieval

For each index, displays:
- ✅/❌ Status (Active/Missing)
- File size (in KB)
- Last modified timestamp
- Quick rebuild button

#### Upload & Rebuild Section
Two-column grid for:
1. **Catalogue Data Upload**
   - Upload catalogue database updates
   - Option to rebuild FAISS index after upload
   - Automatic CSV export from SQLite database

2. **General Queries Upload**
   - Upload `general_queries.json` updates
   - Option to rebuild FAISS index after upload
   - Direct index rebuild from JSON data

#### Information Panel
Explains:
- What FAISS indices are
- How they work in the chatbot
- When to rebuild indices

## Backend Components

### Files Added
1. **`export_catalogue_to_csv.py`**
   - Exports catalogue.db (SQLite) to catalogue.csv
   - Required before building catalogue FAISS index
   - Automatically handles table detection

2. **`catalogue_indexer.py`** (copied from main project)
   - Reads catalogue.csv
   - Generates embeddings using SentenceTransformer
   - Builds FAISS index with L2 similarity
   - Saves to `catalogue_index.faiss`

3. **`build_general_queries_index.py`** (copied from main project)
   - Reads `general_queries.json`
   - Generates embeddings for questions
   - Builds FAISS index
   - Saves to `general_queries_index.faiss`

### PHP Handlers
Located in `admin_enhanced.php`:

#### FAISS Rebuild Handler (Lines ~120-143)
```php
if (isset($_POST['rebuild_faiss'])) {
    $index_type = $_POST['index_type']; // 'catalogue' or 'general'
    
    if ($index_type === 'catalogue') {
        // Export DB to CSV, then build index
        $python_cmd = "cd \"$backend_path\" && python export_catalogue_to_csv.py && python catalogue_indexer.py 2>&1";
    } elseif ($index_type === 'general') {
        $python_cmd = "cd \"$backend_path\" && python build_general_queries_index.py 2>&1";
    }
    
    $output = shell_exec($python_cmd);
    // Check for success indicators
}
```

#### Enhanced Upload Handler (Lines ~66-115)
Now supports:
- `json_type` parameter: 'general_queries', 'website_cache', 'website_analysis', 'catalogue'
- `rebuild_after_upload` checkbox: triggers FAISS rebuild after file upload
- Automatic index rebuild with progress feedback

## Workflow

### Rebuilding Catalogue Index
1. User clicks "🔄 Rebuild" in Catalogue Index row
2. Confirmation dialog appears
3. Backend executes:
   ```bash
   cd backend
   python export_catalogue_to_csv.py    # DB → CSV
   python catalogue_indexer.py          # CSV → FAISS
   ```
4. Success/error message displayed
5. Index status table refreshes

### Rebuilding General Queries Index
1. User clicks "🔄 Rebuild" in General Queries Index row
2. Confirmation dialog appears
3. Backend executes:
   ```bash
   cd backend
   python build_general_queries_index.py  # JSON → FAISS
   ```
4. Success/error message displayed
5. Index status table refreshes

### Upload & Rebuild Workflow
1. User selects JSON file
2. User checks "Rebuild FAISS index after upload"
3. Submit form
4. Backend:
   - Validates JSON format
   - Saves to target path
   - If rebuild checked:
     - Runs appropriate Python script
     - Returns success/failure message
5. Frontend displays combined result

## Data Files

### Catalogue System
- **Source**: `catalogue.db` (SQLite database, 25,196 books)
- **Intermediate**: `catalogue.csv` (exported on-demand)
- **Index**: `catalogue_index.faiss` (38.7 MB)
- **Metadata**: `catalogue_data.pkl` (6.0 MB)

### General Queries System
- **Source**: `general_queries.json` (FAQ data)
- **Index**: `general_queries_index.faiss` (602 KB)
- **Mapping**: `general_queries_mapping.pkl`

### Embedding Model
- **Model**: `all-MiniLM-L6-v2` (SentenceTransformer)
- **Location**: `backend/models/all-MiniLM-L6-v2/`
- **Dimension**: 384
- **Type**: L2 distance (FAISS IndexFlatL2)

## UI Screenshots (Conceptual)

### FAISS Indices Tab
```
🔍 FAISS Index Management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Index Status
┌─────────────────────┬─────────┬──────────┬────────────────────┬─────────┐
│ Index Name          │ Status  │ File Size│ Last Modified      │ Actions │
├─────────────────────┼─────────┼──────────┼────────────────────┼─────────┤
│ Catalogue Index     │ ✅ Active│ 38.7 MB  │ 2024-01-15 10:30   │ 🔄 Rebuild│
│ Book search & recs  │         │          │                    │         │
├─────────────────────┼─────────┼──────────┼────────────────────┼─────────┤
│ General Queries     │ ✅ Active│ 602 KB   │ 2024-01-15 09:15   │ 🔄 Rebuild│
│ Library Q&A KB      │         │          │                    │         │
└─────────────────────┴─────────┴──────────┴────────────────────┴─────────┘

📤 Upload & Rebuild
┌────────────────────────────┬────────────────────────────┐
│ 📚 Catalogue Data          │ ❓ General Queries          │
│                            │                            │
│ [Select catalogue.json]    │ [Select general_queries.json]│
│ ☑ Rebuild after upload     │ ☑ Rebuild after upload     │
│ [📤 Upload & Rebuild]      │ [📤 Upload & Rebuild]      │
└────────────────────────────┴────────────────────────────┘
```

## Error Handling

### Common Issues
1. **Python script not found**
   - Error: "Failed to rebuild index"
   - Solution: Ensure all Python files copied to backend folder

2. **Database missing**
   - Error: "Error: catalogue.db not found"
   - Solution: Copy catalogue.db from main project

3. **Invalid JSON format**
   - Error: "Invalid JSON format"
   - Solution: Validate JSON before upload

4. **Index build timeout**
   - Symptom: Process hangs
   - Solution: Large datasets may take time (up to 5 minutes)

### Success Indicators
The system checks for these strings in Python output:
- "successfully"
- "complete"
- "Indexing completed"

## Testing

### Test Catalogue Index Rebuild
```powershell
cd C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend
python export_catalogue_to_csv.py
python catalogue_indexer.py
```

Expected output:
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

### Test General Queries Index Rebuild
```powershell
cd C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend
python build_general_queries_index.py
```

Expected output:
```
Loading general queries...
Loaded X queries
Generating embeddings...
Building FAISS index...
Saved FAISS index and mapping
Indexing completed successfully!
```

## Performance Notes

### Build Times (Approximate)
- **Catalogue Index**: 2-5 minutes (25K books)
- **General Queries Index**: 10-30 seconds (varies by count)

### Index Sizes
- **Catalogue**: ~40 MB (25K × 384 dims × 4 bytes)
- **General Queries**: ~600 KB (smaller dataset)

### Memory Usage
- **Peak**: ~500 MB during embedding generation
- **Steady**: Minimal (indices loaded on-demand)

## Integration Status

### ✅ Completed
- FAISS Indices tab in admin panel
- Index status display with file info
- Rebuild buttons with confirmation
- Upload & rebuild workflow
- Backend Python scripts (export, indexers)
- Error handling and success messages
- Documentation

### 📝 Related Files Modified
- `frontend/admin_enhanced.php` (added FAISS tab)
- Backend scripts copied:
  - `catalogue_indexer.py`
  - `build_general_queries_index.py`
- New script created:
  - `export_catalogue_to_csv.py`

### 🔗 Dependencies
- Python 3.x
- pandas
- numpy
- sentence-transformers
- faiss-cpu
- sqlite3 (built-in)

## Future Enhancements (Optional)

1. **Progress Bars**: Show real-time indexing progress
2. **Scheduled Rebuilds**: Automatic nightly index updates
3. **Index Comparison**: Before/after statistics
4. **Backup/Restore**: Save index snapshots
5. **Advanced Options**: Configure embedding model, distance metric

## Conclusion

The FAISS management UI provides a streamlined way to maintain semantic search indices without manual terminal commands. Users can now update data sources and rebuild indices directly from the admin panel, matching the functionality available in the Streamlit UI.
