# ATP Application Admin Credentials

## Django Admin Access

### Superuser Account Created ✅

**Username:** `admin`
**Password:** `[REDACTED]`
**Email:** admin@example.com

### Access URLs

- **Admin Panel:** http://localhost:5000/atp/admin/
- **Admin Login:** http://localhost:5000/atp/admin/login/

### Account Details

- **Account Type:** Superuser (Full Access)
- **Permissions:**
  - ✅ Staff status (can access admin panel)
  - ✅ Superuser status (all permissions)
  - ✅ Active status (can login)
- **Created:** October 31, 2025

### What You Can Do in Admin Panel

1. **User Management**
   - Create/Edit/Delete users
   - Manage user permissions
   - Reset passwords
   - View login history

2. **Data Management**
   - Manage Plants
   - View Search History
   - Edit Patterns and Universes
   - View Audit Entries

3. **Documentation**
   - Create/Edit help guides
   - Manage documentation

### Security Notes

⚠️ **IMPORTANT:**
- Change the password immediately in production!
- This is a development password only
- Use strong passwords in production environments

### How to Change Admin Password

```bash
# Via Django Admin:
1. Login to http://localhost:5000/atp/admin/
2. Click on "Users"
3. Click on "admin"
4. Click "Change password form"
5. Enter new password

# Via Command Line:
docker exec -it atp_web python manage.py changepassword admin
```

### How to Create Additional Admin Users

```bash
# Create another superuser
docker exec -it atp_web python manage.py createsuperuser

# Or programmatically
docker exec atp_web python -c "
from django.contrib.auth.models import User
User.objects.create_superuser('newadmin', 'email@example.com', 'password')
"
```

### Database Information

- **Total Users:** 7 (including admin)
- **Database:** MySQL 5.7
- **Database Name:** atp
- **Database User:** dbuser

### Troubleshooting

If you cannot login:

1. **Check services are running:**
   ```bash
   docker-compose -f docker-compose-port5000-fixed.yml ps
   ```

2. **Reset admin password:**
   ```bash
   docker exec atp_web python -c "
   from django.contrib.auth.models import User
   u = User.objects.get(username='admin')
   u.set_password('[REDACTED]')
   u.save()
   print('Password reset')
   "
   ```

3. **Check logs:**
   ```bash
   docker-compose -f docker-compose-port5000-fixed.yml logs web
   ```

---

**Login Now:** http://localhost:5000/atp/admin/
**Username:** admin
**Password:** [REDACTED]