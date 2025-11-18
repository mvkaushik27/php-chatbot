# 📖 Book Search Toggle Feature

## Overview
The Book Search Toggle feature allows administrators to enable or disable book catalogue searching through the admin panel. When disabled, all book-related queries are redirected to general queries, ensuring the chatbot only handles library policies, services, and general information.

## 🎛️ How to Use

### Admin Panel Access
1. Log into the admin panel at `/frontend/admin_enhanced.php`
2. Go to the **System** tab
3. Find the **Book Search Settings** section
4. Toggle the **Book Catalogue Search** switch

### Configuration States

#### ✅ **Book Search ENABLED** (Default)
- Chatbot searches both books and general queries
- Book queries like "machine learning books" return catalogue results
- Full functionality including OPAC integration (if enabled)

#### ❌ **Book Search DISABLED**
- Chatbot only handles general library queries
- Book queries are redirected to general information
- Users get helpful messages about the limitation
- Ideal for maintenance periods or limited-service modes

## 🔧 Technical Implementation

### Backend Configuration
- **Environment Variable**: `NANDU_BOOK_SEARCH` (1=enabled, 0=disabled)
- **Default Value**: Enabled (1)
- **Configuration File**: `backend/.env`

### Admin Panel Functions
- `getBookSearchEnabled()` - Checks current status
- `setBookSearchEnabled($enabled)` - Updates configuration
- Real-time toggle with form submission

### Query Processing Logic
```python
# Classification override
if query_type == 'book' and not _get_book_search_enabled():
    logger.info("📚➡️📋 Book search disabled, treating as general query")
    query_type = 'general'
```

## 📊 Status Monitoring

### Admin Dashboard
The System Configuration Status table shows:
- 📖 Book Catalogue Search: ✅ Enabled / ❌ Disabled  
- 🔍 OPAC Real-time Search: ✅ Enabled / ❌ Disabled

### User Experience
When book search is disabled:
- Book queries receive general library information
- Response includes note: *"Book catalogue search is currently disabled"*
- Users are guided to contact library staff for book-specific queries

## 🧪 Testing

### Test Script
```bash
cd backend
python test_book_search_toggle.py
```

### Manual Testing
1. **Enable book search**: Try "machine learning books" → Should return book results
2. **Disable book search**: Try "machine learning books" → Should return general info with note
3. **General queries**: Try "library timing" → Should work in both modes

## 📝 Use Cases

### When to DISABLE Book Search
- **System Maintenance**: Database updates or OPAC maintenance
- **Limited Service**: During emergencies or reduced staffing
- **Training Mode**: When training staff on general queries only
- **Performance**: To reduce system load during peak usage

### When to ENABLE Book Search
- **Normal Operations**: Full library service availability
- **User Training**: Teaching users how to search the catalogue
- **Research Support**: When users need comprehensive book search

## 🔒 Security & Logging

### Activity Logging
All toggle operations are logged with:
- Admin user identification
- IP address tracking
- Timestamp and action details
- Success/failure status

### Permission Control
- Only authenticated admin users can modify settings
- Changes require form submission with CSRF protection
- Configuration persists across server restarts

## 🚀 Deployment Notes

### Production Setup
1. Set `NANDU_BOOK_SEARCH=1` in production `.env` file
2. Ensure admin credentials are changed from defaults
3. Monitor toggle usage through activity logs
4. Test both states before deployment

### Troubleshooting
- **Toggle not working**: Check `.env` file permissions
- **Changes not persisting**: Verify config file write access
- **Unexpected behavior**: Check `test_book_search_toggle.py` output

---

**Created**: November 2024  
**Version**: 1.0  
**Maintainer**: IIT Ropar Library System  
**Integration**: Nalanda Library Chatbot PHP Admin Panel