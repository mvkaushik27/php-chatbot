# 🧪 Local Testing Setup - Nalanda Library Chatbot (PHP + Python)

Complete local testing environment for the Nalanda Library Chatbot with PHP frontend and Python backend integration.

---

## 📁 Project Structure

```
Nalanda_Chatbot_PHP_Integration/
├── backend/                          # Python API Backend
│   ├── api_server.py                # FastAPI wrapper (created)
│   ├── nandu_brain.py               # Core chatbot logic (copy from main project)
│   ├── formatters.py                # Response formatter (copy from main project)
│   ├── requirements.txt             # Python dependencies
│   ├── catalogue.db                 # SQLite database (copy from main project)
│   ├── general_queries.json         # Q&A JSON (copy from main project)
│   ├── *.faiss, *.pkl               # FAISS indices (copy from main project)
│   ├── models/                      # ML models (copy from main project)
│   └── logs/                        # Audit logs (auto-created)
│
├── frontend/                         # PHP Frontend
│   ├── index.php                    # Main page
│   ├── api/
│   │   └── chat_handler.php         # PHP → Python bridge
│   └── assets/
│       ├── css/
│       │   └── chatbot.css          # Chatbot styles
│       └── js/
│           └── chatbot.js           # Chatbot frontend logic
│
├── start_local_test.bat             # Windows startup script
├── copy_files.ps1                   # PowerShell script to copy files
└── README.md                        # This file
```

---

## 🚀 Quick Start

### **Step 1: Copy Required Files from Main Project**

Run this PowerShell command from the project directory:

```powershell
.\copy_files.ps1
```

Or manually copy these files from `Nalanda_Chatbot\` to `backend\`:
- `nandu_brain.py`
- `formatters.py`
- `catalogue.db`
- `general_queries.json`
- `general_queries_index.faiss`
- `general_queries_mapping.pkl`
- `catalogue_index.faiss`
- `catalogue_mapping.pkl`
- `models/` (entire folder)

### **Step 2: Install Python Dependencies**

```bash
cd backend
pip install -r requirements.txt

# Also install dependencies from main project:
pip install sentence-transformers faiss-cpu scikit-learn beautifulsoup4 textblob groq
```

### **Step 3: Start Servers (Automated)**

Double-click: `start_local_test.bat`

OR manually:

```bash
# Terminal 1 - Python Backend
cd backend
python api_server.py

# Terminal 2 - PHP Frontend (new terminal)
cd frontend
php -S localhost:80
```

### **Step 4: Open Browser**

Navigate to: **http://localhost**

---

## 🧪 Testing Checklist

### ✅ **1. Test Python API Directly**

Open: http://localhost:8000/test

Try these queries:
- "python programming books"
- "library timings"
- "books by Stephen Hawking"
- "how many books can students borrow"

**Expected:** JSON responses with book data or library info

### ✅ **2. Test PHP Frontend**

Open: http://localhost

Click "Chat with Nandu" button and try:
- "machine learning books"
- "library hours"
- "fine policy"
- "access e-journals"

**Expected:** Formatted chat responses in the widget

### ✅ **3. Test Rate Limiting**

Send 25 queries quickly.

**Expected:** After 20 queries:
```
⚠️ Too many requests. Please wait 60 seconds and try again.
```

### ✅ **4. Test Error Handling**

Stop Python backend, then try querying in PHP frontend.

**Expected:** 
```
Chatbot service unavailable. Please ensure the Python API server is running...
```

---

## 🔧 Configuration

### **Change Python API Port**

Edit `backend/api_server.py` (bottom of file):
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Change port here
```

Then update `frontend/api/chat_handler.php`:
```php
$python_api_url = 'http://localhost:8001/chat';  // Match new port
```

### **Change PHP Port**

```bash
php -S localhost:8080  # Use port 8080 instead
```

Then open: http://localhost:8080

---

## 🐛 Troubleshooting

### **Issue 1: "Missing nandu_brain.py"**

**Solution:** Run `copy_files.ps1` or manually copy files from main project.

### **Issue 2: "Port 8000 already in use"**

**Solution:**
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F
```

### **Issue 3: "Cannot connect to Python backend"**

**Symptoms:**
- PHP shows: "Chatbot service unavailable"
- Browser console: "Failed to fetch"

**Solution:**
1. Check Python backend is running: http://localhost:8000/health
2. Check firewall isn't blocking port 8000
3. Verify `chat_handler.php` has correct URL (`http://localhost:8000/chat`)

### **Issue 4: CORS Errors**

**Symptom:** Browser console shows:
```
Access to fetch blocked by CORS policy
```

**Solution:** Ensure `api_server.py` has PHP frontend URL in CORS settings:
```python
allow_origins=[
    "http://localhost:80",
    "http://localhost:8080",
]
```

### **Issue 5: Module Not Found (Python)**

**Symptom:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
cd backend
pip install -r requirements.txt
pip install sentence-transformers faiss-cpu scikit-learn
```

---

## 📊 Architecture Flow

```
1. User types query in PHP frontend
   ↓
2. JavaScript (chatbot.js) sends POST to PHP
   ↓
3. PHP (chat_handler.php) validates and forwards to Python API
   ↓
4. Python (api_server.py) receives request
   ↓
5. Python calls nandu_brain.get_nandu_response()
   ↓
6. nandu_brain.py processes query (classify, search, format)
   ↓
7. Response flows back: Python → PHP → JavaScript → User
```

---

## 🔍 Endpoints Reference

### **Python Backend (Port 8000)**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info and documentation |
| `/chat` | POST | Main chat endpoint (PHP calls this) |
| `/health` | GET | Health check |
| `/stats` | GET | Server statistics |
| `/test` | GET | HTML test page |
| `/docs` | GET | Swagger UI (interactive API docs) |

### **PHP Frontend (Port 80)**

| File | Description |
|------|-------------|
| `/` or `/index.php` | Main page with chatbot widget |
| `/api/chat_handler.php` | Backend handler (JavaScript calls this) |

---

## 📈 Performance Benchmarks

Expected response times:

| Query Type | First Query | Cached Query |
|------------|-------------|--------------|
| Book Search | 1-3 seconds | 0.3-0.5 seconds |
| General Query | 0.5-1 second | 0.1-0.3 seconds |
| Statistics | 0.2-0.5 seconds | 0.1-0.2 seconds |

---

## 🚀 Next Steps

Once local testing works:

1. **Deploy Python Backend** to production server
2. **Update PHP API URL** in `chat_handler.php`
3. **Upload PHP Frontend** to your web server
4. **Configure SSL/HTTPS** for security
5. **Set up monitoring** and logging
6. **Add authentication** if needed

---

## 📞 Support & Debugging

### **Enable Debug Mode**

**PHP:** Edit `chat_handler.php`, uncomment debug section:
```php
// Show detailed errors
error_reporting(E_ALL);
ini_set('display_errors', 1);
```

**Python:** Check terminal where `api_server.py` is running for logs

**JavaScript:** Open browser console (F12) and check:
- Console tab for errors
- Network tab for API calls
- Check request/response details

---

## ✅ Success Criteria

Your setup is working correctly if:

1. ✅ Python backend starts on http://localhost:8000
2. ✅ PHP frontend starts on http://localhost
3. ✅ You can open the chatbot widget
4. ✅ Queries return formatted responses
5. ✅ No CORS errors in browser console
6. ✅ Rate limiting works (blocks after 20 requests)
7. ✅ Health check returns `{"status": "healthy"}`
8. ✅ Response times are acceptable (<3s)

---

## 📝 Files Summary

**Created in this setup:**
- ✅ `backend/api_server.py` - FastAPI wrapper
- ✅ `frontend/index.php` - Main PHP page
- ✅ `frontend/api/chat_handler.php` - PHP middleware
- ✅ `frontend/assets/js/chatbot.js` - Frontend JavaScript
- ✅ `frontend/assets/css/chatbot.css` - Chatbot styles
- ✅ `start_local_test.bat` - Startup script
- ✅ `copy_files.ps1` - File copy script
- ✅ `README.md` - This documentation

**Need to copy from main project:**
- ⏳ `nandu_brain.py` - Core chatbot logic
- ⏳ `formatters.py` - Response formatter
- ⏳ `catalogue.db` - SQLite database
- ⏳ `general_queries.json` - Q&A data
- ⏳ FAISS indices (`.faiss`, `.pkl` files)
- ⏳ `models/` folder - ML models

---

**Happy Testing! 🎉**

For issues or questions, check the troubleshooting section above.
