# 🎨 Visual Setup Guide - Nandu Chatbot PHP Integration

## 📍 Step-by-Step Visual Guide

### **Step 1: Find Your New Folder**

```
📁 C:\Users\Admin\Videos\
   └── 📁 Nalanda_Chatbot_PHP_Integration\  ← Your new testing folder
```

**Location:** `C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\`

---

### **Step 2: Double-Click to Start**

```
📁 Nalanda_Chatbot_PHP_Integration\
   ├── 📄 start_local_test.bat  ← DOUBLE-CLICK THIS!
   ├── 📄 QUICK_START.md
   ├── 📄 README.md
   └── ...
```

**What Happens:**
```
┌─────────────────────────────────────┐
│  Terminal 1: Python Backend Opens   │
│  🐍 Starting on port 8000...        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Terminal 2: PHP Frontend Opens     │
│  🔧 Starting on port 80...          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Browser: Opens Automatically       │
│  🌐 http://localhost                │
└─────────────────────────────────────┘
```

---

### **Step 3: See the Interface**

```
┌──────────────────────────────────────────────────────────┐
│  📚 IIT Ropar Library                                    │
│  Welcome to the Nalanda Library Assistance System        │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Library Information                                      │
│  The Central Library at IIT Ropar provides access...     │
│                                                           │
│  [📖 OPAC] [🌐 Library Website] [✉️ Contact Us]        │
│                                                           │
└──────────────────────────────────────────────────────────┘

                                    ┌───────────────────────┐
                                    │ 💬 Chat with Nandu    │ ← CLICK HERE
                                    └───────────────────────┘
```

---

### **Step 4: Chat Widget Opens**

```
                            ┌─────────────────────────────────┐
                            │ 🤖 Nandu - Library Assistant  × │
                            ├─────────────────────────────────┤
                            │                                 │
                            │  🤖 Nandu:                     │
                            │  Hello! I'm Nandu, your        │
                            │  library assistant. I can help:│
                            │  • 🔍 Search for books         │
                            │  • ⏰ Check library hours      │
                            │  • 📖 Learn borrowing rules    │
                            │                                 │
                            ├─────────────────────────────────┤
                            │ [Auto ▼] [Type here...] [Send] │
                            └─────────────────────────────────┘
```

---

### **Step 5: Type and Get Response**

```
You type: "python books"

┌─────────────────────────────────────┐
│ You: python books                   │
├─────────────────────────────────────┤
│ 🤖 Nandu:                          │
│ 📚 I found 12 books matching       │
│ 'python'                            │
│                                     │
│ 1. Python Programming (2023)       │
│    Author: John Doe                 │
│    Call No: 005.133 DOE            │
│    Status: Available ✅            │
│                                     │
│ 2. Learning Python (2022)          │
│    Author: Jane Smith              │
│    Call No: 005.133 SMI            │
│    Status: Available ✅            │
│                                     │
│ [View in OPAC]                     │
└─────────────────────────────────────┘
```

---

## 🎯 What You'll See in Terminals

### **Terminal 1: Python Backend**

```
====================================
🚀 Starting Nandu Brain API Server
====================================
📖 API Docs: http://localhost:8000/docs
🧪 Test Page: http://localhost:8000/test
🏥 Health Check: http://localhost:8000/health
====================================

INFO:     Started server process [12345]
INFO:     Waiting for application startup.
2025-11-10 08:00:00,000 [INFO] 🚀 Initializing Nandu Brain module...
2025-11-10 08:00:00,100 [INFO] 🔄 Loading SentenceTransformer model...
2025-11-10 08:00:03,500 [INFO] ✅ SentenceTransformer loaded in 3.40s
2025-11-10 08:00:03,500 [INFO] ✅ Nandu Brain initialization complete
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000

# When you send a query:
2025-11-10 08:01:00,000 [INFO] 📥 Query from 127.0.0.1: 'python books'
2025-11-10 08:01:01,200 [INFO] ✅ Response generated in 1.20s
```

---

### **Terminal 2: PHP Frontend**

```
PHP 8.x Development Server (http://localhost:80) started

# When you send a query:
[Sun Nov 10 08:01:00 2025] 127.0.0.1:52345 [200]: GET /
[Sun Nov 10 08:01:00 2025] 127.0.0.1:52346 [200]: POST /api/chat_handler.php
```

---

## 🌐 URLs You Can Access

```
┌──────────────────────────────────────────────────────────┐
│  FRONTEND (What Users See)                               │
├──────────────────────────────────────────────────────────┤
│  http://localhost                                         │
│  → Main page with chatbot widget                         │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  BACKEND (Developer Tools)                                │
├──────────────────────────────────────────────────────────┤
│  http://localhost:8000                                    │
│  → API info page                                          │
│                                                           │
│  http://localhost:8000/test                              │
│  → Quick test page (no PHP needed)                       │
│                                                           │
│  http://localhost:8000/docs                              │
│  → Interactive API documentation                         │
│                                                           │
│  http://localhost:8000/health                            │
│  → Health check (JSON response)                          │
└──────────────────────────────────────────────────────────┘
```

---

## 📊 File Tree (What Was Created)

```
C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\
│
├── 📂 backend\                       Python Backend
│   ├── 📄 api_server.py             FastAPI server ✨ NEW
│   ├── 📄 nandu_brain.py            Brain logic ✅ Copied
│   ├── 📄 formatters.py             Formatter ✅ Copied
│   ├── 📄 catalogue.db              SQLite DB ✅ Copied
│   ├── 📄 general_queries.json      Q&A ✅ Copied
│   ├── 📄 *.faiss, *.pkl            Indices ✅ Copied
│   ├── 📄 requirements.txt          Dependencies ✨ NEW
│   ├── 📂 models\                   ML models ✅ Copied
│   └── 📂 logs\                     Auto-created
│
├── 📂 frontend\                      PHP Frontend
│   ├── 📄 index.php                 Main page ✨ NEW
│   ├── 📂 api\
│   │   └── 📄 chat_handler.php      PHP bridge ✨ NEW
│   └── 📂 assets\
│       ├── 📂 css\
│       │   └── 📄 chatbot.css       Styles ✨ NEW
│       └── 📂 js\
│           └── 📄 chatbot.js        Logic ✨ NEW
│
├── 📄 start_local_test.bat          Startup script ✨ NEW
├── 📄 copy_files.ps1                File copier ✨ NEW
├── 📄 README.md                     Full docs ✨ NEW
├── 📄 QUICK_START.md                Quick guide ✨ NEW
├── 📄 PROJECT_SUMMARY.md            Overview ✨ NEW
├── 📄 VISUAL_GUIDE.md               This file ✨ NEW
└── 📄 folder_structure.txt          Tree view ✨ NEW
```

---

## 🎬 Demo Flow

```
1. User Opens Browser
   ↓
2. Sees Library Homepage
   ↓
3. Clicks "Chat with Nandu" Button
   ↓
4. Chat Widget Slides In
   ↓
5. User Types: "machine learning books"
   ↓
6. JavaScript Sends to PHP
   ↓
7. PHP Forwards to Python API
   ↓
8. Python Processes (1-2 seconds)
   ↓
9. Response Flows Back
   ↓
10. Chat Widget Shows Results
```

**Total Time:** 1-3 seconds from query to response!

---

## 🎨 Color Scheme

The chatbot uses a professional blue theme:

```
Primary Blue:    #1976d2  ███ Headers, buttons
Darker Blue:     #1565c0  ███ Hover states
Light Blue:      #e3f2fd  ███ User messages
White:           #ffffff  ███ Bot messages
Background:      #f5f5f5  ███ Chat area
Success Green:   #4caf50  ███ Bot message border
Error Red:       #dc3545  ███ Error messages
Warning Yellow:  #ffc107  ███ Loading messages
```

---

## 📱 Responsive Design

### **Desktop (> 500px):**
```
┌────────────────────────────────────┐
│  Library Homepage                  │
│                                    │
│  [Content]                         │
│                                    │
│                    [Chat Button]   │  ← Bottom right
└────────────────────────────────────┘
```

### **Mobile (< 500px):**
```
┌──────────────────┐
│  Library         │
│  Homepage        │
│                  │
│  [Content]       │
│                  │
│  [Chat]          │  ← Full screen
└──────────────────┘
```

---

## 🚦 Status Indicators

```
🟢 GREEN  = Healthy, Running
🟡 YELLOW = Loading, Processing
🔴 RED    = Error, Failed
⚪ GRAY   = Disabled, Inactive
```

---

## ✅ Success Checklist (Visual)

```
☑️ Folder created at: Nalanda_Chatbot_PHP_Integration\
☑️ Files copied from main project
☑️ New files created (12 files)
☑️ Startup script ready
☑️ Documentation complete
☑️ Python backend configured
☑️ PHP frontend configured
☑️ All systems ready to test!
```

---

## 🎯 Ready to Start?

1. **Navigate to:** `C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\`
2. **Double-click:** `start_local_test.bat`
3. **Wait for:** Browser to open
4. **Click:** "💬 Chat with Nandu"
5. **Type:** Your first query!

---

**That's it! Enjoy testing your chatbot! 🎉**
