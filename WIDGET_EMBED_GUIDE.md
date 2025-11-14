# Nalanda Library Chatbot - Widget Embedding Guide

## 🎯 Quick Embed (Copy-Paste Method)

Add this code **before the closing `</body>` tag** of your library website:

```html
<!-- Nalanda Library Chatbot Widget -->
<script src="https://your-domain.com/widget-embed.js"></script>
```

---

## 📋 Full Embed Code (Self-Contained)

If you prefer to host the widget yourself, copy this entire code block before the closing `</body>` tag:

```html
<!-- Nalanda Library Chatbot Widget - START -->
<div id="nalanda-chatbot-container"></div>
<link rel="stylesheet" href="https://your-php-backend.com/frontend/assets/css/widget.css">
<script>
(function() {
    // Load widget HTML
    fetch('https://your-php-backend.com/frontend/widget.html')
        .then(response => response.text())
        .then(html => {
            document.getElementById('nalanda-chatbot-container').innerHTML = html;
        });
})();
</script>
<!-- Nalanda Library Chatbot Widget - END -->
```

---

## 🔧 Advanced: Inline Embed (No External Dependencies)

For maximum compatibility, paste this **complete standalone code** before `</body>`:

```html
<!-- Nalanda Chatbot Widget - Standalone -->
<style>
.nalanda-chatbot-widget * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', sans-serif;
}
.nalanda-chatbot-widget {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9999;
}
.nalanda-chat-toggle-btn {
    padding: 15px 25px;
    background: linear-gradient(90deg, #10b981, #0f766e);
    color: white;
    border: none;
    border-radius: 24px;
    font-size: 16px;
    font-weight: 500;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    transition: transform 0.2s, box-shadow 0.2s;
}
.nalanda-chat-toggle-btn:hover {
    background: linear-gradient(90deg, #059669, #0d9488);
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
}
.nalanda-chat-window {
    position: fixed;
    bottom: 80px;
    right: 20px;
    width: 420px;
    height: 600px;
    background: white;
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    display: none;
    flex-direction: column;
    overflow: hidden;
}
.nalanda-chat-window.active { display: flex; }
.nalanda-chat-header {
    background: linear-gradient(90deg, #10b981, #0f766e);
    color: white;
    padding: 15px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.nalanda-chat-header h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
}
.nalanda-chat-close-btn {
    background: none;
    border: none;
    color: white;
    font-size: 28px;
    cursor: pointer;
    line-height: 1;
}
.nalanda-chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    background: #fafafa;
}
.nalanda-chat-message {
    margin-bottom: 15px;
    display: flex;
    flex-direction: column;
}
.nalanda-message-bubble {
    padding: 12px 16px;
    border-radius: 18px;
    max-width: 80%;
    word-wrap: break-word;
}
.nalanda-user-message .nalanda-message-bubble {
    background: white;
    align-self: flex-end;
    margin-left: auto;
    border: 1px solid #e5e7eb;
}
.nalanda-bot-message .nalanda-message-bubble {
    background: white;
    align-self: flex-start;
    border-left: 3px solid #10b981;
}
.nalanda-chat-input-container {
    padding: 15px;
    background: white;
    border-top: 1px solid #e5e7eb;
}
.nalanda-chat-input-wrapper {
    display: flex;
    gap: 10px;
}
.nalanda-chat-input {
    flex: 1;
    padding: 10px 15px;
    border: 1px solid #d1d5db;
    border-radius: 20px;
    font-size: 14px;
    outline: none;
}
.nalanda-chat-input:focus {
    border-color: #10b981;
    box-shadow: 0 0 0 1px #10b981;
}
.nalanda-chat-send-btn {
    padding: 10px 20px;
    background: linear-gradient(90deg, #10b981, #0f766e);
    color: white;
    border: none;
    border-radius: 20px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
}
.nalanda-chat-send-btn:hover {
    background: linear-gradient(90deg, #059669, #0d9488);
}
@media (max-width: 768px) {
    .nalanda-chat-window {
        width: calc(100vw - 40px);
        height: calc(100vh - 100px);
    }
}
</style>

<div class="nalanda-chatbot-widget">
    <button id="nalanda-chat-toggle" class="nalanda-chat-toggle-btn">
        💬 Chat with Nalanda Library
    </button>
    <div id="nalanda-chat-window" class="nalanda-chat-window">
        <div class="nalanda-chat-header">
            <h3>🎓 Nalanda Library Chatbot</h3>
            <button id="nalanda-chat-close" class="nalanda-chat-close-btn">×</button>
        </div>
        <div id="nalanda-chat-messages" class="nalanda-chat-messages">
            <div class="nalanda-chat-message nalanda-bot-message">
                <div class="nalanda-message-bubble">
                    👋 Hello! I'm the Nalanda Library Chatbot. How can I help you today?
                </div>
            </div>
        </div>
        <div class="nalanda-chat-input-container">
            <div class="nalanda-chat-input-wrapper">
                <input type="text" id="nalanda-chat-input" class="nalanda-chat-input" 
                       placeholder="Ask about books, timings, services..." autocomplete="off">
                <button id="nalanda-chat-send" class="nalanda-chat-send-btn">Send</button>
            </div>
        </div>
    </div>
</div>

<script>
(function() {
    const API_URL = 'http://localhost:8000/chat'; // Update with your backend URL
    
    const toggleBtn = document.getElementById('nalanda-chat-toggle');
    const chatWindow = document.getElementById('nalanda-chat-window');
    const closeBtn = document.getElementById('nalanda-chat-close');
    const messagesContainer = document.getElementById('nalanda-chat-messages');
    const inputField = document.getElementById('nalanda-chat-input');
    const sendBtn = document.getElementById('nalanda-chat-send');

    toggleBtn.addEventListener('click', () => {
        chatWindow.classList.add('active');
        inputField.focus();
    });

    closeBtn.addEventListener('click', () => {
        chatWindow.classList.remove('active');
    });

    function sendMessage() {
        const message = inputField.value.trim();
        if (!message) return;

        addMessage(message, 'user');
        inputField.value = '';

        fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: message })
        })
        .then(res => res.json())
        .then(data => {
            const answer = data.answer || data.response || 'Sorry, I could not process your request.';
            addMessage(answer, 'bot');
        })
        .catch(err => {
            console.error('Error:', err);
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        });
    }

    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `nalanda-chat-message nalanda-${sender}-message`;
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'nalanda-message-bubble';
        bubbleDiv.textContent = text;
        messageDiv.appendChild(bubbleDiv);
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    sendBtn.addEventListener('click', sendMessage);
    inputField.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
})();
</script>
<!-- Nalanda Chatbot Widget - END -->
```

---

## ⚙️ Configuration

### Update Backend API URL

In the widget code, find this line and update it with your actual backend URL:

```javascript
const API_URL = 'http://localhost:8000/chat'; // ← Change this
```

**Examples:**
- Production: `https://library.iitrpr.ac.in/chatbot/api/chat`
- Local: `http://localhost:8000/chat`
- PHP Backend: `https://your-domain.com/backend/api_server.php`

---

## 🎨 Customization Options

### Change Button Text
```javascript
// In the HTML, find:
<button id="nalanda-chat-toggle" class="nalanda-chat-toggle-btn">
    💬 Chat with Nalanda Library  ← Change this text
</button>
```

### Change Position
```css
/* Move to left side */
.nalanda-chatbot-widget {
    bottom: 20px;
    left: 20px;  /* Change from 'right' to 'left' */
}
```

### Change Colors
Replace the gradient colors in CSS:
```css
/* Primary color */
background: linear-gradient(90deg, #10b981, #0f766e);

/* Hover color */
background: linear-gradient(90deg, #059669, #0d9488);
```

---

## 🧪 Testing

1. **Open your website in a browser**
2. **Look for the chat button** in the bottom-right corner
3. **Click the button** to open the chat window
4. **Type a message** and press Enter or click Send
5. **Check the browser console** (F12) for any errors

---

## 🔒 Security Notes

- Always use HTTPS in production
- Set proper CORS headers on your backend
- Sanitize user inputs on the backend
- Rate limit API requests

---

## 📱 Mobile Responsive

The widget automatically adapts to mobile screens:
- **Desktop**: 420px × 600px floating window
- **Mobile**: Full-screen overlay (with margins)

---

## 🆘 Troubleshooting

### Widget not appearing?
- Check browser console for JavaScript errors
- Verify the code is placed before `</body>`
- Ensure no CSS conflicts with class names

### Chat not responding?
- Verify API_URL is correct
- Check backend is running and accessible
- Look for CORS errors in browser console
- Test API endpoint directly using Postman

### Styling issues?
- Add `!important` to widget CSS rules if needed
- Check for conflicting CSS on the main website
- Use browser DevTools to inspect elements

---

## 📞 Support

For issues or questions:
- Email: mahavir@iitrpr.ac.in
- Check backend logs: `backend/api_server.log`

---

## 🚀 Deployment Checklist

- [ ] Update `API_URL` to production backend
- [ ] Test on staging website first
- [ ] Verify HTTPS connections
- [ ] Test on mobile devices
- [ ] Check page load performance
- [ ] Monitor backend API logs
- [ ] Set up error tracking (optional)

---

**Version**: 1.0  
**Last Updated**: November 2025  
**Maintained by**: IIT Ropar Library Team
