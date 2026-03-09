# Export Download & Notification System - Test Plan

## Pre-Test Checklist

✅ All containers running: `docker-compose -f docker-compose-port5000-secure.yml ps`
✅ Application accessible: http://localhost:5000
✅ User logged in: admin/DummyPass123!
✅ Browser console open (F12) - watch for errors

---

## Test 1: Bell Icon and Basic UI

### Steps:
1. Navigate to http://localhost:5000/atp/chat/
2. Look at the top navbar

### Expected Results:
- ✅ Bell icon (🔔) visible between "AI Search" and folder icon
- ✅ Folder icon visible before "Help"
- ✅ No badge visible initially (no unread notifications)
- ✅ Icons styled with ARC Brand_D colors

### How to Verify:
- Check browser console: Should see `[Notifications] Initializing...`
- Check browser console: Should see `[Notifications] Polling started (5s interval)`
- Watch Network tab: Should see request to `/atp/chat/notifications/` every 5 seconds

---

## Test 2: Create an Export (Small Query)

### Steps:
1. In chat, type: **"List all products in plant 9993"**
2. Wait for results (should be < 200 products)
3. Click **"Email Results"** button
4. Confirm email modal opens
5. Email address should be pre-filled with your user email
6. Click **"Send Email"**

### Expected Results:
- ✅ Success message: "Report emailed to [email]. Check the bell icon for download link."
- ✅ Within 5 seconds, bell icon badge appears showing "1"
- ✅ Badge has red background with pulse animation

### How to Verify:
- Check browser console for notification fetch
- Open browser Network tab and look for `/atp/chat/notifications/` response
- Should see JSON with your notification

---

## Test 3: View Notification and Download

### Steps:
1. Click the bell icon (🔔)
2. Dropdown panel should appear
3. Look for notification showing your export
4. Click **"Download"** button

### Expected Results:
- ✅ Dropdown opens showing notification panel
- ✅ Panel shows: "Export ready: X products"
- ✅ Shows timestamp ("Just now" or "1 minute ago")
- ✅ Download button visible with product count
- ✅ Clicking Download opens new tab with CSV file
- ✅ CSV file downloads successfully
- ✅ After download, badge count updates to "0"
- ✅ Notification disappears from panel

### How to Verify:
- Check browser Downloads folder for CSV file
- Open CSV and verify product data is present
- Check browser console: `[Notifications] Marked notification X as read`

---

## Test 4: Large Query (200+ Products)

### Steps:
1. In chat, type: **"List all flatware products"**
2. Wait for choice prompt (should show 200+ products detected)
3. Click **"Email All"** button
4. Wait 30-60 seconds for processing

### Expected Results:
- ✅ Choice prompt appears: "Show First 200" vs "Email All"
- ✅ Processing message: "This may take 30-60 seconds..."
- ✅ Success message: "Complete report emailed... Check the bell icon..."
- ✅ Bell badge updates to show "1" (or increments if already had notifications)

### How to Verify:
- Watch the chat for progress messages
- Check email inbox for actual email with CSV attachment
- Bell badge should light up when complete

---

## Test 5: Export History Page

### Steps:
1. Click the folder icon (📁) in the navbar
2. Page should navigate to Export History

### Expected Results:
- ✅ Page title: "My Export History"
- ✅ Shows all your past exports
- ✅ Each export shows:
  - Filename
  - Status badge (green "Success")
  - Product count
  - Recipient email
  - Timestamp ("2 minutes ago")
  - Your username
  - Download button
- ✅ Bell badge updates to "0" (all notifications marked read)

### How to Verify:
- Count number of export cards matches number of exports you created
- Click any Download button - should download CSV
- Go back to chat page - bell badge should still show "0"

---

## Test 6: Multiple Notifications

### Steps:
1. Create 3 exports quickly:
   - "Show stock for product 10001"
   - "Show stock for product 12345"
   - "Show stock for product 99999"
2. Email each result
3. Watch the bell icon

### Expected Results:
- ✅ Badge updates: "1" → "2" → "3"
- ✅ Click bell to see all 3 notifications listed
- ✅ "Mark all read" button visible
- ✅ Click "Mark all read" → all disappear, badge shows "0"

### How to Verify:
- Each notification has its own Download button
- All timestamps are different
- Product counts are correct

---

## Test 7: Security - Download Permission

### Steps:
1. Note an export ID from your history (e.g., export ID 5)
2. Log out
3. Log in as different user (or create new user)
4. Try to access: http://localhost:5000/atp/chat/download/5/

### Expected Results:
- ✅ Should see error: "You do not have permission to download this file"
- ✅ Status code: 403 Forbidden

### How to Verify:
- Check Docker logs: `docker-compose -f docker-compose-port5000-secure.yml logs web | tail -20`
- Should see security warning: `[SECURITY] User attempted to download export belonging to...`

---

## Test 8: Admin Access

### Steps:
1. Log in as admin (admin/DummyPass123!)
2. Navigate to Export History
3. Should see ALL exports from ALL users

### Expected Results:
- ✅ Shows exports from multiple users (if any)
- ✅ Blue info alert: "Admin View: You're seeing all exports..."
- ✅ Can download any export (even from other users)

### How to Verify:
- Check `User` column in export cards
- Should see different usernames if multiple users have exported

---

## Test 9: Cleanup Command (Dry Run)

### Steps:
1. Run cleanup in dry-run mode:
```bash
docker exec atp_web python manage.py cleanup_exports --dry-run
```

### Expected Results:
```
Export Cleanup Starting...
Retention period: 7 days
Cutoff date: 2025-10-29 XX:XX:XX
----------------------------------------------------------------------

[DRY RUN] - No changes made

Would delete:
  • X export records
  • X files from disk
  • Associated notifications
```

### How to Verify:
- No files actually deleted
- Export History still shows all exports
- Shows what WOULD be deleted if run for real

---

## Test 10: Cleanup Command (Real)

### Steps:
1. Create a test export
2. Manually set its date to 8 days ago:
```bash
docker exec atp_web python manage.py shell
from chatbot.models import EmailAuditLog
from django.utils import timezone
from datetime import timedelta
old_export = EmailAuditLog.objects.last()
old_export.sent_at = timezone.now() - timedelta(days=8)
old_export.save()
exit()
```

3. Run cleanup:
```bash
docker exec atp_web python manage.py cleanup_exports
```

### Expected Results:
```
✓ Cleanup Complete!

Deleted:
  • 1 export records
  • 1 files from disk
  • X notifications
```

### How to Verify:
- Export no longer appears in history
- File deleted from disk
- Notification removed

---

## Test 11: Notification Panel Click Outside

### Steps:
1. Click bell icon to open panel
2. Click anywhere outside the panel

### Expected Results:
- ✅ Panel closes automatically
- ✅ Badge still shows correct count

### How to Verify:
- Click bell again - panel reopens with same notifications

---

## Test 12: Browser Console Check

### Steps:
1. Open browser console (F12)
2. Watch for 30 seconds

### Expected Results:
- ✅ No JavaScript errors
- ✅ Polling requests every 5 seconds: `[Notifications] Fetching...`
- ✅ No 404 or 500 errors in Network tab
- ✅ All CSS loaded properly (no missing Bootstrap Icons)

### How to Verify:
- Console tab: No red errors
- Network tab: All requests return 200 OK
- Elements tab: Bell icon shows `<i class="bi bi-bell-fill"></i>`

---

## Test 13: Responsive Design

### Steps:
1. Open browser DevTools (F12)
2. Toggle device toolbar (mobile view)
3. Try different screen sizes

### Expected Results:
- ✅ Bell icon remains visible on mobile
- ✅ Notification panel adjusts to screen size
- ✅ Export History page remains readable
- ✅ Download buttons accessible on touch devices

### How to Verify:
- Test on actual phone/tablet if available
- No horizontal scrolling required
- All buttons tappable with finger

---

## Test 14: Performance

### Steps:
1. Open browser Performance tab
2. Record a session while:
   - Opening notification panel
   - Downloading a file
   - Viewing history page
3. Stop recording and analyze

### Expected Results:
- ✅ Page load < 3 seconds
- ✅ Notification fetch < 500ms
- ✅ Download starts immediately
- ✅ No memory leaks from polling

### How to Verify:
- Check Network waterfall for slow requests
- Monitor memory usage over time
- No steadily increasing memory usage

---

## Test 15: Error Handling

### Steps:
1. Stop web container: `docker-compose -f docker-compose-port5000-secure.yml stop web`
2. Watch browser console
3. Start web container: `docker-compose -f docker-compose-port5000-secure.yml start web`

### Expected Results:
- ✅ Console shows: `[Notifications] Error fetching: HTTP 502/503`
- ✅ Bell icon doesn't crash
- ✅ When container restarts, polling resumes automatically
- ✅ No user-visible errors (graceful degradation)

### How to Verify:
- Application continues working after restart
- No need to refresh page
- Notifications resume within 5 seconds

---

## Regression Tests

### Ensure Old Features Still Work:

1. **Regular Export (< 200 products)**
   - Search for single product
   - Email results
   - Verify email received

2. **Large Query Flow**
   - Search for 200+ products
   - Choose "Show First 200"
   - Verify only 200 shown
   - Verify message: "Showing first 200 of X total products"

3. **Choice Buttons**
   - Large query shows choice
   - "Show First 200" button works
   - "Email All" button works

4. **Session Management**
   - New Chat clears conversation
   - Previous chats load from sidebar
   - Delete session works

5. **Admin Panel**
   - http://localhost:5000/atp/admin/
   - Navigate to Email Audit Logs
   - Can see export records
   - Can see Export Notifications
   - csv_file field shows file path

---

## Performance Benchmarks

### Expected Timings:
- **Notification fetch**: < 200ms
- **Download start**: < 500ms
- **History page load**: < 1s
- **Polling overhead**: < 1% CPU
- **Memory usage**: Stable (no growth over time)

### Test:
```bash
# Monitor CPU/Memory
docker stats atp_web

# Test notification endpoint speed
time curl -s http://localhost:5000/atp/chat/notifications/ -H "Cookie: sessionid=YOUR_SESSION"
```

---

## Known Limitations

1. **Polling vs WebSockets**: Uses 5-second polling (simpler but less real-time)
2. **File Retention**: 7 days default (configurable)
3. **Notification Limit**: Shows max 10 recent (prevents UI clutter)
4. **History Limit**: 50 for users, 100 for admins
5. **Browser Support**: Requires modern browser (ES6 support)

---

## Troubleshooting

### Bell Icon Not Showing
```bash
# Check Bootstrap Icons loaded
curl -I https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css

# Clear browser cache
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)
```

### Notifications Not Updating
```bash
# Check endpoint
curl http://localhost:5000/atp/chat/notifications/ -H "Cookie: sessionid=YOUR_SESSION"

# Check logs
docker-compose -f docker-compose-port5000-secure.yml logs web | grep NOTIFICATION
```

### Download Fails
```bash
# Check files exist
docker exec atp_web ls -la /app/media/email_exports/

# Check permissions
docker exec atp_web stat /app/media/email_exports/
```

### Cleanup Not Working
```bash
# Test with dry-run
docker exec atp_web python manage.py cleanup_exports --dry-run --days 1

# Check dates
docker exec atp_web python manage.py shell -c "from chatbot.models import EmailAuditLog; from django.utils import timezone; print([(e.id, e.sent_at, timezone.now() - e.sent_at) for e in EmailAuditLog.objects.all()[:5]])"
```

---

## Success Criteria

✅ All 15 tests pass
✅ No console errors
✅ All downloads work
✅ Notifications appear within 5 seconds
✅ Badge counts are accurate
✅ History page shows all exports
✅ Cleanup command works
✅ Security checks prevent unauthorized access
✅ No memory leaks
✅ Application remains responsive

**Status:** Ready for Production Testing! 🚀

---

## Quick Test Commands

```bash
# Check everything is running
docker-compose -f docker-compose-port5000-secure.yml ps

# Watch logs in real-time
docker-compose -f docker-compose-port5000-secure.yml logs -f web

# Test notification API directly
curl http://localhost:5000/atp/chat/notifications/

# Count unread notifications
docker exec atp_web python manage.py shell -c "from chatbot.models import ExportNotification; print(f'Unread: {ExportNotification.objects.filter(is_read=False).count()}')"

# List recent exports
docker exec atp_web python manage.py shell -c "from chatbot.models import EmailAuditLog; [print(f'{e.id}: {e.csv_filename} - {e.sent_at}') for e in EmailAuditLog.objects.order_by('-sent_at')[:5]]"

# Test cleanup (dry-run)
docker exec atp_web python manage.py cleanup_exports --dry-run

# Restart if needed
docker-compose -f docker-compose-port5000-secure.yml restart web nginx
```

---

## Report Issues

If any test fails, include:
1. Test number that failed
2. Screenshot of error
3. Browser console output
4. Docker logs: `docker-compose logs web > error.log`
5. Steps to reproduce
