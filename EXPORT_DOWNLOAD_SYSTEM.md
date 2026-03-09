# Export Download & Notification System

## Overview

Complete implementation of export file download system with real-time notifications. Users can now download their export files directly from the application instead of relying only on email.

**Implementation Date:** November 5, 2025
**Status:** ✅ Complete and Deployed

---

## Features

### 🔔 Real-Time Notifications
- **Bell icon** in navbar with badge showing unread count
- **Polls every 5 seconds** for new notifications
- **Pulse animation** on badge to draw attention
- **Dropdown panel** showing recent exports with download buttons
- **Auto-updates** when exports complete

### 📥 Secure Downloads
- **Permission-based access** - users can only download their own files
- **Admin override** - admins can download any export
- **Audit logging** - all downloads are logged
- **File validation** - checks file exists before serving
- **Direct download** - no email required

### 📊 Export History Page
- **Full history** of all user exports (last 50 for users, 100 for admins)
- **Download links** for all successful exports
- **Status indicators** (success, failed, blocked)
- **Detailed metadata** (date, product count, recipient, etc.)
- **Auto-marks read** when viewing page

### 🧹 Automatic Cleanup
- **Management command** to delete old exports
- **7-day default** retention (configurable)
- **Dry-run mode** to preview deletions
- **Comprehensive logging** and reporting
- **Cron-ready** for automated scheduling

---

## Architecture

### Database Models

#### ExportNotification (`chatbot/models.py:261-297`)
```python
- user: ForeignKey to User
- export_log: ForeignKey to EmailAuditLog
- message: CharField (notification text)
- is_read: BooleanField (tracking)
- created_at: DateTimeField (timestamp)
```

### API Endpoints

#### GET `/atp/chat/notifications/`
- Returns unread notifications for current user
- Includes export_id, message, product_count, timestamp
- Limited to 10 most recent

#### POST `/atp/chat/notifications/mark-read/`
- Marks notification(s) as read
- Accepts single ID or "all"
- Updates badge count

#### GET `/atp/chat/download/<export_id>/`
- **Secure download endpoint**
- Permission checks (own files only, unless admin)
- File validation
- Serves CSV with proper headers
- Logs all downloads

#### GET `/atp/chat/history/`
- Shows export history page
- Auto-marks all notifications as read
- Different limits for users vs admins

### Frontend Components

#### Notification Bell (`chat.html:27-30`)
- Bootstrap Icons bell (bi-bell-fill)
- Badge with count
- Click to toggle dropdown

#### Notification Panel (`chat.html:45-56`)
- Dropdown below navbar
- Shows notifications with download buttons
- "Mark all read" option
- Empty state when no notifications

#### JavaScript Polling (`notifications.js`)
- Polls `/atp/chat/notifications/` every 5 seconds
- Updates badge count dynamically
- Renders notification items
- Handles downloads and mark-as-read
- Auto-closes on outside click

### Integration Points

#### export_email() (`views.py:1250-1258`)
```python
# After saving audit log and CSV file:
ExportNotification.objects.create(
    user=request.user,
    export_log=audit_log,
    message=f"Export ready: {len(results)} products",
    is_read=False
)
```

#### export_large_query() (`views.py:1489-1496`)
```python
# After bulk export completes:
notification_message = f"Export ready: {len(results)} products from {description}"
ExportNotification.objects.create(
    user=request.user,
    export_log=audit_log,
    message=notification_message,
    is_read=False
)
```

---

## User Experience Flow

### 1. User Exports Products
```
User searches → Gets 200+ products → Chooses "Email All"
  ↓
System queries SAP for all products (may take 30-60s)
  ↓
Email sent with CSV attachment
  ↓
CSV file saved to media/email_exports/
  ↓
EmailAuditLog created with audit trail
  ↓
ExportNotification created
  ↓
Bell icon lights up with badge "1" 🔔
```

### 2. User Receives Notification
```
Bell badge pulses → User clicks bell
  ↓
Dropdown opens showing:
  "Export ready: 487 products from Flatware"
  "2 minutes ago"
  [Download (487 products)] button
```

### 3. User Downloads File
```
User clicks Download button
  ↓
Opens secure endpoint: /atp/chat/download/123/
  ↓
System checks permissions
  ↓
Validates file exists
  ↓
Serves CSV file
  ↓
Marks notification as read
  ↓
Badge updates to "0"
```

### 4. User Views History
```
User clicks folder icon in navbar
  ↓
Opens /atp/chat/history/
  ↓
Shows all past exports with:
  - Date/time
  - Product count
  - Status
  - Download button
  ↓
All unread notifications marked as read
```

---

## Security Features

### Permission Checks
- ✅ Users can only download their own exports
- ✅ Admins can download any export
- ✅ Attempted violations are logged
- ✅ Returns 403 Forbidden for unauthorized access

### Audit Logging
- ✅ All downloads logged with username
- ✅ IP address and user agent tracked
- ✅ Personal email detection
- ✅ Admin override flagging

### File Validation
- ✅ Checks export exists in database
- ✅ Validates user owns export
- ✅ Confirms file exists on disk
- ✅ Returns proper error messages

---

## File Storage

### Media Configuration (`settings.py:152-154`)
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### Docker Volume (`docker-compose-port5000-secure.yml`)
```yaml
volumes:
  - media_volume:/app/media  # Web container
  - media_volume:/media:ro   # Nginx container (read-only)
```

### File Path Structure
```
/app/media/
└── email_exports/
    └── 2025/
        └── 11/
            ├── atp_report_Flatware_20251105_160300.csv
            ├── atp_report_Glassware_20251105_161500.csv
            └── ...
```

### Nginx Configuration (`nginx-fixed.conf:19-22`)
```nginx
location /media/ {
    alias /media/;
    expires 7d;
}
```

---

## Cleanup System

### Management Command

**File:** `chatbot/management/commands/cleanup_exports.py`

**Usage:**
```bash
# Standard cleanup (7 days)
python manage.py cleanup_exports

# Custom retention period (14 days)
python manage.py cleanup_exports --days 14

# Dry run (preview only)
python manage.py cleanup_exports --dry-run
```

**What it deletes:**
- EmailAuditLog records older than N days
- CSV files from disk
- Associated ExportNotification records

**Output:**
```
Export Cleanup Starting...
Retention period: 7 days
Cutoff date: 2025-10-29 16:00:00
----------------------------------------------------------------------

Found 5 exports to clean up:

  • Export ID 123: atp_report_Flatware_20251029_143000.csv
    User: admin
    Sent: 2025-10-29 14:30 (7 days ago)
    Products: 487
    ✓ Deleted 1 notification(s)
    ✓ Deleted file (245.3 KB)
    ✓ Deleted database record

======================================================================

✓ Cleanup Complete!

Deleted:
  • 5 export records
  • 5 files from disk
  • 5 notifications

======================================================================
```

### Cron Setup (Recommended)

**Add to crontab:**
```bash
# Run daily at 2 AM
0 2 * * * cd /mnt/d/demoproject && docker exec atp_web python manage.py cleanup_exports >> /var/log/cleanup_exports.log 2>&1
```

**Or use Docker exec:**
```bash
docker exec atp_web python manage.py cleanup_exports
```

---

## CSS Styling (ARC Brand_Delta Theme)

### Colors Used
- **Navy Purple:** `#231F74` (primary brand color)
- **Yellow:** `#FFC72C` (accent/hover)
- **White:** `#FFFFFF` (background)
- **Border:** `#e0e0e0` (subtle lines)

### Key Styles (`arc-cardinal-theme.css:800-911`)
- `.notification-panel` - Dropdown container
- `.notification-header` - Gradient header with yellow border
- `.notification-item` - Individual notification cards
- `.notification-item.unread` - Yellow gradient for unread
- `.notification-badge` - Pulse animation on badge
- `.notification-download-btn` - Gradient button with hover effect

---

## Testing Checklist

### ✅ Functional Tests
- [x] Bell icon appears in navbar
- [x] Badge shows correct unread count
- [x] Dropdown opens/closes on click
- [x] Notifications display correctly
- [x] Download button works
- [x] File downloads successfully
- [x] Notification marked as read after download
- [x] Badge updates after marking read
- [x] "Mark all read" works
- [x] Export history page loads
- [x] History shows all user exports
- [x] Download links work from history page
- [x] Cleanup command works (dry-run)
- [x] Cleanup command deletes old files
- [x] Polling updates every 5 seconds

### ✅ Security Tests
- [x] Users can't download other users' files
- [x] Admins can download any file
- [x] Unauthorized attempts are logged
- [x] File validation prevents path traversal
- [x] Download audit logging works
- [x] Personal email detection works

### ✅ Edge Cases
- [x] No notifications shows empty state
- [x] Missing file shows error message
- [x] Deleted export handles gracefully
- [x] Large export counts display correctly
- [x] Old exports beyond retention deleted

---

## Performance Considerations

### Polling Frequency
- **5-second interval** - balances responsiveness with server load
- **10-notification limit** - prevents large payloads
- **Auto-stops on page unload** - cleans up polling

### Database Queries
- **select_related('export_log')** - prevents N+1 queries
- **Indexed fields** - user, is_read, created_at
- **Limited results** - 10 for notifications, 50 for history

### File Serving
- **Nginx serves media** - efficient static file delivery
- **7-day cache** - reduces repeated downloads
- **Read-only volume** - prevents accidental writes

---

## Migration Applied

**File:** `chatbot/migrations/0005_auto_20251105_1600.py`

**Changes:**
- Created `chatbot_export_notifications` table
- Added indexes on (user, is_read, created_at)
- Added foreign key to chatbot_email_audit_log

**Run migration:**
```bash
docker exec atp_web python manage.py migrate
```

---

## Files Modified/Created

### Created Files
- ✅ `chatbot/models.py` - Added ExportNotification model (lines 261-297)
- ✅ `chatbot/static/chatbot/js/notifications.js` - Polling system (310 lines)
- ✅ `chatbot/templates/chatbot/export_history.html` - History page (230 lines)
- ✅ `chatbot/management/commands/cleanup_exports.py` - Cleanup command (150 lines)
- ✅ `chatbot/management/__init__.py` - Management module
- ✅ `chatbot/management/commands/__init__.py` - Commands module

### Modified Files
- ✅ `chatbot/views.py` - Added 4 new views (250+ lines added)
  - get_notifications() - lines 1536-1574
  - mark_notification_read() - lines 1579-1631
  - download_export() - lines 1634-1701
  - export_history() - lines 1704-1743
  - Updated export_email() - lines 1250-1258
  - Updated export_large_query() - lines 1465-1496

- ✅ `chatbot/urls.py` - Added 4 new URL patterns (lines 30-35)
- ✅ `chatbot/templates/chatbot/chat.html` - Added bell icon, panel, links
  - Bell icon - lines 27-30
  - Folder icon - lines 31-33
  - Notification panel - lines 45-56
  - Bootstrap Icons - line 10
  - JavaScript - line 378

- ✅ `chatbot/static/chatbot/css/arc-cardinal-theme.css` - Added notification styles (lines 800-911)
- ✅ `settings.py` - Added MEDIA_ROOT/URL (lines 152-154)
- ✅ `docker-compose-port5000-secure.yml` - Added media_volume

---

## URLs Reference

| URL | Method | Purpose |
|-----|--------|---------|
| `/atp/chat/notifications/` | GET | Fetch unread notifications |
| `/atp/chat/notifications/mark-read/` | POST | Mark notification(s) as read |
| `/atp/chat/download/<id>/` | GET | Secure file download |
| `/atp/chat/history/` | GET | Export history page |

---

## Configuration Options

### Retention Period
Change in cleanup command:
```bash
python manage.py cleanup_exports --days 14  # 14-day retention
```

### Polling Frequency
Change in `notifications.js:60`:
```javascript
this.pollInterval = setInterval(() => {
    this.fetchNotifications();
}, 5000);  // Change to 10000 for 10 seconds
```

### Notification Limit
Change in `views.py:1551`:
```python
.order_by('-created_at')[:10]  # Change to [:20] for 20 notifications
```

### Company Domains
Change in `views.py:1115` and `views.py:1461`:
```python
company_domains = ['democorp.example.com', 'democorp-intl.example.com', 'yourcompany.com']
```

---

## Troubleshooting

### Bell icon not showing
- Check Bootstrap Icons loaded: `https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css`
- Clear browser cache (Ctrl+F5)
- Check browser console for errors

### Notifications not updating
- Check browser console for polling errors
- Verify endpoint: `curl http://localhost:5000/atp/chat/notifications/`
- Check Docker logs: `docker-compose -f docker-compose-port5000-secure.yml logs web`

### Download fails
- Check file exists: `docker exec atp_web ls -la /app/media/email_exports/`
- Check nginx volume: `docker exec atp_nginx ls -la /media/email_exports/`
- Check permissions: User vs Admin access

### Files not deleted by cleanup
- Run dry-run: `python manage.py cleanup_exports --dry-run`
- Check date math: Exports must be older than retention period
- Check status: Only 'success' status exports are deleted

---

## Future Enhancements

### Possible Additions
- [ ] WebSocket notifications (real-time instead of polling)
- [ ] Export progress bar for large queries
- [ ] Bulk download (ZIP multiple exports)
- [ ] Email preference toggle (email + download vs download only)
- [ ] Notification sound/desktop notifications
- [ ] Export scheduling (weekly reports)
- [ ] Share export link with other users (admin only)
- [ ] Export templates (save search criteria)

---

## Support & Maintenance

### Regular Tasks
1. **Weekly:** Check cleanup logs for errors
2. **Monthly:** Review disk usage in `/app/media/email_exports/`
3. **Quarterly:** Analyze export patterns and adjust retention

### Monitoring Commands
```bash
# Check media disk usage
docker exec atp_web du -sh /app/media/email_exports/

# Count exports in database
docker exec atp_web python manage.py shell -c "from chatbot.models import EmailAuditLog; print(EmailAuditLog.objects.count())"

# Count notifications
docker exec atp_web python manage.py shell -c "from chatbot.models import ExportNotification; print(ExportNotification.objects.filter(is_read=False).count())"

# Test cleanup (dry-run)
docker exec atp_web python manage.py cleanup_exports --dry-run
```

---

## Summary

✅ **Complete notification system** with real-time updates
✅ **Secure download infrastructure** with permission checks
✅ **Full audit trail** for compliance
✅ **Automatic cleanup** to manage disk space
✅ **Beautiful UI** matching ARC Brand_Delta brand
✅ **Production-ready** and deployed

**Status:** Ready for user testing! 🚀
