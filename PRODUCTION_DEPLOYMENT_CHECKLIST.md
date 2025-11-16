# 🚀 Production Deployment Checklist

## ⚠️ CRITICAL Security Changes Required

### 1. Update Admin Password
```php
// In frontend/admin_enhanced.php
define('ADMIN_PASSWORD', 'YOUR_STRONG_PASSWORD_HERE'); // Change from 'admin123'
```

### 2. Update API URLs
```javascript
// In frontend/widget.html (line 583-585)
const API_URL = 'https://library.iitrpr.ac.in/api/chat'; // Update your domain
```

```php
// In frontend/api/chat_handler.php (line 70)
$python_api_url = 'https://library.iitrpr.ac.in/api/chat'; // Update your domain
```

### 3. Configure CORS for Production
```python
# In backend/api_server.py - Update these domains:
allow_origins=[
    "https://library.iitrpr.ac.in",    # Your library website
    "https://www.iitrpr.ac.in",        # Main website
    # Remove localhost origins in production
]
```

### 4. Enable HTTPS Only
- Deploy backend with SSL certificate
- Update all HTTP URLs to HTTPS
- Test SSL certificate validity

## 📋 Deployment Steps

### Backend Deployment (Python API)
1. **Install dependencies on server:**
   ```bash
   pip install -r backend/requirements.txt
   pip install sentence-transformers faiss-cpu scikit-learn beautifulsoup4 textblob groq
   ```

2. **Use production ASGI server:**
   ```bash
   # Install production server
   pip install gunicorn uvicorn[standard]
   
   # Run with gunicorn (recommended)
   cd backend
   gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

3. **Set up process manager (systemd/supervisor)**
4. **Configure reverse proxy (nginx/apache) with SSL**

### Frontend Deployment (PHP Widget)
1. **Upload files to web server:**
   - `frontend/widget.html` → Public web directory
   - `frontend/admin_enhanced.php` → Secure admin directory
   - `frontend/api/chat_handler.php` → If using PHP proxy

2. **Update file permissions:**
   ```bash
   chmod 644 widget.html
   chmod 600 admin_enhanced.php  # Restrict admin access
   ```

### Widget Integration Methods

#### Method 1: Embed Script (Recommended)
Add to your website before `</body>`:
```html
<script>
fetch('https://library.iitrpr.ac.in/widget.html')
    .then(r => r.text())
    .then(html => {
        document.body.insertAdjacentHTML('beforeend', html);
    });
</script>
```

#### Method 2: Direct Embed
Copy entire `widget.html` content into your website template.

#### Method 3: iFrame
```html
<iframe src="https://library.iitrpr.ac.in/widget.html" 
        style="position:fixed;bottom:0;right:0;border:none;width:450px;height:650px;z-index:9999;">
</iframe>
```

## 🔒 Production Security Checklist

- [ ] **Change admin password** from 'admin123'
- [ ] **Update API URLs** to production domains
- [ ] **Configure CORS** for specific domains only
- [ ] **Enable HTTPS** everywhere
- [ ] **Set up SSL certificates**
- [ ] **Configure rate limiting** (currently 20 req/min)
- [ ] **Set up monitoring** and logging
- [ ] **Test from actual website**
- [ ] **Test on mobile devices**
- [ ] **Backup configuration files**

## 🔧 Environment Configuration

Create `.env` file in backend:
```env
NANDU_WEBSCRAPE=1
RATE_LIMIT_REQUESTS=20
RATE_LIMIT_WINDOW=60
```

## 📊 Performance Optimization

1. **Optimize model loading** (models cache automatically)
2. **Use CDN** for static files if needed
3. **Enable gzip compression** on web server
4. **Monitor response times** (should be <3 seconds)

## 🧪 Testing Before Go-Live

### Functionality Testing
- [ ] OPAC toggle works in admin panel
- [ ] Real-time availability shows correctly
- [ ] Due dates display for issued books
- [ ] Rate limiting blocks excessive requests
- [ ] Mobile responsiveness works
- [ ] All browsers supported (Chrome, Firefox, Safari, Edge)

### Security Testing
- [ ] Admin panel requires authentication
- [ ] API endpoints reject malformed requests
- [ ] CORS blocks unauthorized domains
- [ ] Rate limiting prevents abuse
- [ ] Error messages don't leak sensitive info

### Performance Testing
- [ ] Widget loads in <2 seconds
- [ ] Chat responses in <3 seconds
- [ ] No JavaScript errors in console
- [ ] Memory usage stable under load

## 🆘 Rollback Plan

Keep backup of:
- [ ] Original `widget.html` with localhost URLs
- [ ] Backend configuration files
- [ ] Admin panel without new features

## 📞 Support Information

- **Developer**: mahavir@iitrpr.ac.in
- **Logs Location**: `backend/logs/`
- **Admin Panel**: `/admin_enhanced.php`
- **API Health Check**: `/health` endpoint

---

**Last Updated**: November 2025  
**Version**: 1.0 Production Ready