# 🎯 QUICK START GUIDE - 3 Steps to Test Locally

## ⚡ Quick Setup (5 Minutes)

### Step 1: Open Project Folder
```
Navigate to: C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\
```

### Step 2: Double-Click This File
```
start_local_test.bat
```

### Step 3: Use the Chatbot
```
Browser will open automatically at: http://localhost
Click "Chat with Nalanda Library Chatbot" and start chatting!
```

---

## 📋 What Gets Started

1. **Python Backend API** → http://localhost:8000
   - Handles all AI/ML processing
   - Processes chatbot queries
   - Manages database and FAISS search

2. **PHP Frontend Server** → http://localhost:80
   - Displays the chatbot UI
   - Handles user interactions
   - Communicates with Python backend

---

## 🧪 Test Pages

| Page | URL | Purpose |
|------|-----|---------|
| **Main Chatbot** | http://localhost | Full PHP frontend with chat widget |
| **Python API Test** | http://localhost:8000/test | Direct API testing |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health Check** | http://localhost:8000/health | Backend status |

---

## 💬 Try These Queries

### Book Searches:
- "python programming books"
- "machine learning textbooks"
- "books by Stephen Hawking"
- "artificial intelligence books"

### Library Information:
- "library timings"
- "how many books can I borrow"
- "fine policy"
- "library rules"

### Services:
- "access e-journals"
- "how to search books"
- "contact library"

---

## 🛑 To Stop Servers

**Press any key** in the startup window, or:

```powershell
# Manually kill processes
taskkill /FI "WINDOWTITLE eq Nalanda*" /F
```

---

## ⚠️ Troubleshooting

### Problem: "Python not found"
**Solution:** Install Python 3.9+ from https://www.python.org/

### Problem: "PHP not found"
**Solution:** Install PHP from https://www.php.net/downloads

### Problem: "Module not found"
**Solution:**
```bash
cd backend
pip install -r requirements.txt
pip install sentence-transformers faiss-cpu scikit-learn
```

### Problem: "Port already in use"
**Solution:**
```bash
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Problem: "Cannot connect to backend"
**Check:**
1. Is Python backend running? → http://localhost:8000/health
2. Firewall blocking port 8000?
3. Both servers started successfully?

---

## 📊 Expected Output

### When You Start `start_local_test.bat`:
```
====================================
  Nalanda Library Chatbot - Local Testing
  PHP Frontend + Python Backend
====================================

[INFO] Python and PHP detected successfully
[1/5] Checking Python dependencies...
[2/5] Starting Python Backend API...
[3/5] Starting PHP Built-in Server...
[4/5] Waiting for servers to start...
[5/5] Opening Browser...

====================================
  Servers Started Successfully!
====================================

Python Backend: http://localhost:8000
PHP Frontend:   http://localhost

Press any key to STOP all servers...
```

### In Browser (http://localhost):
- You'll see a nice library homepage
- Bottom right: "💬 Chat with Nalanda Library Chatbot" button
- Click it to open the chat widget
- Type your query and get instant responses!

---

## ✅ Success Indicators

You know it's working when:
- ✅ Two terminal windows open (Python + PHP)
- ✅ Browser opens automatically
- ✅ Chat widget appears and opens
- ✅ Queries return formatted responses
- ✅ No error messages in browser console (F12)

---

## 🚀 Next Steps

Once you confirm local testing works:

1. Deploy Python backend to your production server
2. Update PHP `chat_handler.php` with production API URL
3. Upload PHP files to your institute's web server
4. Configure SSL/HTTPS
5. Go live!

---

## 📞 Need Help?

Check:
1. README.md - Full documentation
2. Browser console (F12) - JavaScript errors
3. Python terminal - Backend logs
4. PHP terminal - Frontend requests

---

**Ready? Double-click `start_local_test.bat` now!** 🚀
