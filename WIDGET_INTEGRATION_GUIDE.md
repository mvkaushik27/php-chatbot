# Widget Integration Guide

## 🚀 Quick Start - Getting the Widget to Work

### Prerequisites Checklist:
- ✅ Python backend API running on port 8000
- ✅ Web server (PHP or any) serving the frontend folder
- ✅ CORS enabled on backend (if accessing from different domain)

---

## 🔧 Step 1: Start the Python Backend

The widget needs the Python backend API to be running to get chatbot responses.

```powershell
# Navigate to backend folder
cd C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend

# Start the API server
python api_server.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!** The server must stay running.

---

## 🌐 Step 2: Serve the Widget

You have **3 options** to access the widget:

### **Option A: Direct File Access (Quick Test)**
```
file:///C:/Users/Admin/Videos/Nalanda_Chatbot_PHP_Integration/frontend/widget.html
```

⚠️ **Important:** File protocol has CORS restrictions. The API calls may fail.
✅ **Solution:** Use Option B or C instead.

### **Option B: PHP Development Server (Recommended)**
```powershell
# Navigate to frontend folder
cd C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\frontend

# Start PHP server on port 8080
php -S localhost:8080
```

**Access widget at:** `http://localhost:8080/widget.html`

### **Option C: Python HTTP Server (Alternative)**
```powershell
# Navigate to frontend folder
cd C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\frontend

# Start Python server on port 8080
python -m http.server 8080
```

**Access widget at:** `http://localhost:8080/widget.html`

---

## 🧪 Step 3: Test the Widget

1. **Open the widget URL** in your browser
2. **Click the chat button** (bottom-right corner)
3. **Type a test message:** "library hours"
4. **Press Enter** or click Send
5. **Wait for response** (should appear in 1-2 seconds)

### Expected Behavior:
- ✅ Chat window opens
- ✅ Your message appears on the right (white bubble)
- ✅ Typing indicator shows (3 dots)
- ✅ Bot response appears on the left (with green border)

### If Nothing Happens:
1. **Open browser console** (F12 → Console tab)
2. **Look for error messages**
3. **Common issues:**
   - `Failed to fetch` → Backend not running
   - `CORS error` → Need to enable CORS (see below)
   - `404 Not Found` → Wrong API URL

---

## 🔍 Troubleshooting

### Issue 1: "Failed to fetch" Error

**Cause:** Backend API server is not running

**Solution:**
```powershell
cd C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\backend
python api_server.py
```

### Issue 2: CORS Error

**Cause:** Browser blocking cross-origin requests

**Solution:** Enable CORS in `backend/api_server.py`

Check if this code exists (around line 30-40):
```python
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

If missing, add it after `app = FastAPI()`.

### Issue 3: Empty Response

**Cause:** API responding but widget not displaying it

**Solution:** Check browser console for the actual response:
```javascript
// In browser console (F12), type:
fetch('http://localhost:8000/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query: 'test'})
})
.then(r => r.json())
.then(d => console.log(d))
```

Should show: `{answer: "..."}`

### Issue 4: API URL Wrong

**Solution:** Update API_URL in widget.html (line ~297):

```javascript
// For local development
const API_URL = 'http://localhost:8000/chat';

// For production (update domain)
const API_URL = 'https://library.iitrpr.ac.in/api/chat';
```

---

## 🎯 Integration into Existing Website

### Method 1: iframe Embed (Easiest)

Add this to your library website HTML:

```html
<iframe 
    src="http://your-server.com/widget.html" 
    style="position:fixed;bottom:0;right:0;border:none;width:450px;height:650px;z-index:9999;"
    allow="microphone">
</iframe>
```

### Method 2: Direct Embed (Full Control)

Copy the entire content of `widget.html` and paste it into your website before `</body>`.

**Important:** Update the API_URL to match your backend:
```javascript
const API_URL = 'https://your-domain.com/api/chat';
```

### Method 3: External Script (Clean)

1. Host `widget.html` on your server
2. Add this script to your website:

```html
<script>
fetch('https://your-server.com/widget.html')
    .then(r => r.text())
    .then(html => {
        document.body.insertAdjacentHTML('beforeend', html);
    });
</script>
```

---

## ⚙️ Configuration Options

### Change API Endpoint

In `widget.html`, find and update:
```javascript
const API_URL = 'http://localhost:8000/chat';  // ← Change this
```

### Change Widget Position

In `widget.html` CSS, find `.nalanda-chatbot-widget` and change:
```css
.nalanda-chatbot-widget {
    position: fixed;
    bottom: 20px;  /* Distance from bottom */
    right: 20px;   /* Distance from right */
    /* For left side, use: left: 20px; */
}
```

### Change Colors

Already updated to your theme:
- Header: `linear-gradient(90deg, #059669, #0d9488)` ✅
- Chat Background: `#e3f2fd` ✅

---

## 🔒 Security Checklist

- [ ] Update `allow_origins` in CORS to specific domains (not "*")
- [ ] Use HTTPS in production
- [ ] Set rate limiting on backend API
- [ ] Sanitize user inputs on backend
- [ ] Enable API authentication if needed

---

## 📊 Monitoring

### Check Backend Logs
```powershell
# Backend terminal shows all requests
INFO:     127.0.0.1:xxxxx - "POST /chat HTTP/1.1" 200 OK
```

### Check Browser Console
```
F12 → Console tab
Look for fetch requests and responses
```

### Test API Directly
```powershell
# Using curl
curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d '{\"query\":\"library hours\"}'

# Should return: {"answer":"..."}
```

---

## 🚀 Production Deployment

### 1. Update API URL in widget.html:
```javascript
const API_URL = 'https://library.iitrpr.ac.in/api/chat';
```

### 2. Deploy Backend:
- Host Python API on a server
- Use production ASGI server (gunicorn + uvicorn)
- Configure HTTPS
- Set up process manager (systemd/supervisor)

### 3. Deploy Frontend:
- Upload widget.html to your web server
- Ensure it's accessible via HTTPS
- Update paths if needed

### 4. Test:
- Test from actual library website
- Check all browsers (Chrome, Firefox, Safari, Edge)
- Test on mobile devices

---

## 📞 Quick Reference

| Component | URL | Status Check |
|-----------|-----|--------------|
| **Python Backend** | http://localhost:8000 | `http://localhost:8000/test` |
| **PHP Frontend** | http://localhost:8080 | `http://localhost:8080/index.php` |
| **Widget** | http://localhost:8080/widget.html | Open in browser |
| **Admin Panel** | http://localhost:8080/admin_enhanced.php | Login required |

---

## 🆘 Still Not Working?

Run this diagnostic script:

```powershell
Write-Host "`n=== Widget Diagnostic ===" -ForegroundColor Cyan

# Check Backend
$backend = Test-NetConnection -ComputerName localhost -Port 8000 -InformationLevel Quiet
Write-Host "Backend (port 8000): $(if($backend){'✅ Running'}else{'❌ Not Running'})"

# Check Frontend
$frontend = Test-NetConnection -ComputerName localhost -Port 8080 -InformationLevel Quiet
Write-Host "Frontend (port 8080): $(if($frontend){'✅ Running'}else{'❌ Not Running'})"

# Check Files
$widgetExists = Test-Path "C:\Users\Admin\Videos\Nalanda_Chatbot_PHP_Integration\frontend\widget.html"
Write-Host "Widget file: $(if($widgetExists){'✅ Exists'}else{'❌ Missing'})"

# Test API
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/test" -UseBasicParsing
    Write-Host "API Response: ✅ $($response.StatusCode)"
} catch {
    Write-Host "API Response: ❌ Failed"
}

Write-Host "`nNext Steps:"
if (-not $backend) { Write-Host "  1. Start backend: cd backend; python api_server.py" }
if (-not $frontend) { Write-Host "  2. Start frontend: cd frontend; php -S localhost:8080" }
Write-Host "  3. Open: http://localhost:8080/widget.html"
Write-Host ""
```

---

**Last Updated:** November 2025  
**Support:** mahavir@iitrpr.ac.in
