# Security Deployment Checklist for ATP Application

## ✅ Pre-Deployment Security Checklist

### 🔐 Critical Security Items (MUST DO)

#### 1. Environment Variables (.env file)
- [ ] **Generate new Django SECRET_KEY**
  ```bash
  python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
- [ ] **Update .env file with new SECRET_KEY**
- [ ] **Change DATABASE_PASSWORD** from default `DummyPass123!`
- [ ] **Change SAP_PASSWORD** from default `DummyPass123!`
- [ ] **Change MYSQL_ROOT_PASSWORD** from default `DummyPass123!`
- [ ] **Set DJANGO_DEBUG=False**
- [ ] **Verify .env is in .gitignore**

#### 2. File Permissions
- [ ] Ensure .env file has restricted permissions: `chmod 600 .env`
- [ ] Verify settings.ini is not accessible via web
- [ ] Check that log directories exist with proper permissions

#### 3. Django Settings Verification
- [ ] Confirm settings_secure.py is being used
- [ ] Verify DEBUG is False in production
- [ ] Check ALLOWED_HOSTS includes only your domains
- [ ] Ensure security middleware is active

### 📋 Implementation Status

#### Security Files Created
- [x] `.env` - Environment configuration (CHANGE PASSWORDS!)
- [x] `settings_secure.py` - Secure Django settings
- [x] `middleware.py` - Security headers and logging
- [x] `validators.py` - Input validation functions
- [x] `connection.py` - Secure SAP connection handler
- [x] `docker-compose-secure.yml` - Secure Docker configuration
- [x] `nginx-secure.conf` - Hardened nginx configuration
- [x] `Dockerfile-secure` - Security-enhanced Docker image
- [x] `wsgi_secure.py` - Secure WSGI configuration
- [x] `manage_secure.py` - Management script with secure settings

#### Code Modifications
- [x] Updated `views.py` to use environment variables for SAP connection
- [x] Added input validation to prevent injection attacks
- [x] Implemented rate limiting
- [x] Added security headers middleware
- [x] Enhanced logging for security events

## 🚀 Deployment Instructions

### Step 1: Prepare Environment (5 minutes)

```bash
# 1. Navigate to project directory
cd /opt/app

# 2. Create .env from example (if not exists)
cp .env.example .env

# 3. Generate new SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 4. Edit .env file
nano .env
# Update:
#   - DJANGO_SECRET_KEY=<generated key>
#   - DATABASE_PASSWORD=<new strong password>
#   - SAP_PASSWORD=<new SAP password>
#   - MYSQL_ROOT_PASSWORD=<new root password>

# 5. Set proper permissions
chmod 600 .env
```

### Step 2: Update Database Passwords (10 minutes)

```bash
# 1. Connect to MySQL
docker-compose exec db mysql -u root -p

# 2. Change djangoadmin password
ALTER USER 'djangoadmin'@'%' IDENTIFIED BY 'YOUR_NEW_PASSWORD';
FLUSH PRIVILEGES;

# 3. Update .env with new password
```

### Step 3: Update SAP Password (5 minutes)

1. Contact SAP administrator to change password for user `DummyPass123!`
2. Update SAP_PASSWORD in .env file
3. Test connection with test_sap_connection.py

### Step 4: Deploy with Docker (15 minutes)

```bash
# 1. Stop current containers
docker-compose down

# 2. Backup current data
docker-compose exec db mysqldump -u djangoadmin -p atp > backup_$(date +%Y%m%d).sql

# 3. Use secure Docker configuration
cp docker-compose-secure.yml docker-compose.yml
cp Dockerfile-secure Dockerfile
cp nginx-secure.conf nginx.conf

# 4. Rebuild with security patches
docker-compose build --no-cache

# 5. Start services
docker-compose up -d

# 6. Check logs
docker-compose logs -f
```

### Step 5: Verify Security (10 minutes)

```bash
# 1. Test application is running
curl http://localhost/

# 2. Check security headers
curl -I http://localhost/

# 3. Verify DEBUG is False
docker-compose exec web python manage_secure.py shell
>>> from django.conf import settings
>>> print(settings.DEBUG)  # Should be False

# 4. Check logs are being created
ls -la /var/log/gunicorn/

# 5. Test login rate limiting
# Try logging in multiple times quickly - should get rate limited
```

## 🔒 Security Features Implemented

### 1. Authentication & Authorization
- ✅ Session timeout (1 hour)
- ✅ HTTP-only cookies
- ✅ CSRF protection
- ✅ Password complexity requirements
- ✅ Login attempt logging

### 2. Input Validation
- ✅ Plant code validation
- ✅ Material number validation
- ✅ Search pattern sanitization
- ✅ SQL injection prevention
- ✅ XSS protection

### 3. Security Headers
- ✅ X-Content-Type-Options: nosniff
- ✅ X-Frame-Options: DENY
- ✅ X-XSS-Protection: 1; mode=block
- ✅ Content-Security-Policy
- ✅ Referrer-Policy

### 4. Rate Limiting
- ✅ Login endpoint: 5 requests/minute
- ✅ General API: 100 requests/minute
- ✅ IP-based tracking

### 5. Logging & Monitoring
- ✅ Authentication events
- ✅ Failed login attempts
- ✅ Admin access logging
- ✅ SAP interaction logging
- ✅ Security violation logging

### 6. Infrastructure Security
- ✅ Environment-based configuration
- ✅ Docker security best practices
- ✅ Non-root user in container
- ✅ Network isolation
- ✅ Health checks

## ⚠️ Important Reminders

### Before Going Live
1. **CHANGE ALL DEFAULT PASSWORDS**
2. **Set up SSL/HTTPS certificates**
3. **Configure firewall rules**
4. **Set up backup strategy**
5. **Configure monitoring alerts**
6. **Review and update ALLOWED_HOSTS**
7. **Test disaster recovery procedure**

### Ongoing Security Maintenance
- [ ] Weekly: Review security logs
- [ ] Monthly: Update dependencies
- [ ] Quarterly: Security audit
- [ ] Yearly: Penetration testing

## 🔥 Quick Rollback Plan

If issues occur after deployment:

```bash
# 1. Restore previous Docker images
docker-compose down
git checkout HEAD~1 docker-compose.yml Dockerfile
docker-compose up -d

# 2. Restore database if needed
docker-compose exec db mysql -u root -p atp < backup_YYYYMMDD.sql

# 3. Restore previous settings
cp atp/atp/settings.py.backup atp/atp/settings.py
docker-compose restart web
```

## 📊 Verification Tests

### Test 1: Security Headers
```bash
curl -I http://localhost/ | grep -E "X-Content-Type|X-Frame|X-XSS"
```
Expected: Should see security headers

### Test 2: Debug Mode
```bash
curl http://localhost/nonexistent-page/
```
Expected: Generic 404 page (not Django debug page)

### Test 3: Rate Limiting
```bash
for i in {1..10}; do curl -X POST http://localhost/atp/login/; done
```
Expected: Should get rate limited after 5 attempts

### Test 4: Input Validation
```bash
curl "http://localhost/atp/search/?product='; DROP TABLE users--"
```
Expected: Should reject with validation error

## 📝 Final Notes

1. **This setup maintains Python 3.6 compatibility** for your pyrfc wheel
2. **All security patches are backward compatible**
3. **Settings.ini is kept as fallback** for gradual migration
4. **Monitor logs closely** for the first 24 hours after deployment
5. **Keep this checklist** for future security audits

## ✅ Sign-off

- [ ] All passwords changed from defaults
- [ ] Security patches deployed successfully
- [ ] Application tested and working
- [ ] Logs being generated
- [ ] Team notified of changes
- [ ] Documentation updated

**Deployment Date**: _______________
**Deployed By**: _______________
**Verified By**: _______________

---

## Need Help?

If you encounter issues:
1. Check logs: `docker-compose logs web`
2. Verify environment: `docker-compose exec web env | grep -E "DJANGO|SAP|DATABASE"`
3. Test connectivity: `python test_sap_connection.py`
4. Review this checklist

**Remember: Security is an ongoing process, not a one-time fix!**