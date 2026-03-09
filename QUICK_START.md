# ATP Application - Quick Start Guide

**For developers who need to get up and running quickly**

---

## Prerequisites
- Docker & Docker Compose installed
- Ollama installed on Windows with `atp-chatbot` model
- WSL2 (if on Windows)

## 5-Minute Setup

### 1. Start the Application
```bash
cd /mnt/d/demoproject
docker-compose -f docker-compose-port5000-secure.yml up -d
```

### 2. Wait 30 Seconds
Database needs time to initialize on first run.

### 3. Access the Application
Open browser: **http://localhost:5000/**

### 4. Login
- Username: `admin`
- Password: `[REDACTED]`

### 5. Try the AI Chat
Go to: **http://localhost:5000/atp/chat/**

Test queries:
- "What's the stock of product 10001?"
- "What's the UPC?" (tests context memory)
- "Do the same with 10002" (tests action repeat)

---

## Common Commands

### Start/Stop
```bash
# Start
docker-compose -f docker-compose-port5000-secure.yml up -d

# Stop
docker-compose -f docker-compose-port5000-secure.yml down

# Restart
docker-compose -f docker-compose-port5000-secure.yml restart
```

### View Logs
```bash
# All logs
docker-compose -f docker-compose-port5000-secure.yml logs -f

# Web app only
docker-compose -f docker-compose-port5000-secure.yml logs -f web

# Last 50 lines
docker-compose -f docker-compose-port5000-secure.yml logs --tail=50
```

### Check Status
```bash
docker-compose -f docker-compose-port5000-secure.yml ps
```

---

## Application URLs

| Service | URL |
|---------|-----|
| Home Page | http://localhost:5000/ |
| Login | http://localhost:5000/atp/login/ |
| Product Search | http://localhost:5000/atp/search/ |
| AI Chat | http://localhost:5000/atp/chat/ |
| Admin Panel | http://localhost:5000/atp/admin/ |

---

## Troubleshooting

### Chat Not Working?
```bash
# Check Ollama is running (on Windows)
ollama list

# Should show: atp-chatbot

# Test model
echo "Test" | ollama run atp-chatbot

# Check web logs
docker-compose -f docker-compose-port5000-secure.yml logs web | grep Ollama
```

### SAP Connection Issues?
Check credentials in `atp/atp/settings_secure.py`:
```python
SAP_CONFIG = {
    'ashost': 'sap-server-address',
    'sysnr': '00',
    'client': '100',
    'user': 'your-username',
    'passwd': 'your-password',
}
```

### Database Issues?
```bash
# Reset database (WARNING: Deletes all data!)
docker-compose -f docker-compose-port5000-secure.yml down -v
docker-compose -f docker-compose-port5000-secure.yml up -d
```

### Can't Login?
```bash
# Create new superuser
docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py createsuperuser
```

---

## Development Workflow

### Make Code Changes
1. Edit files in `atp/` directory
2. Restart web container:
   ```bash
   docker-compose -f docker-compose-port5000-secure.yml restart web
   ```

### Update AI Model
1. Edit `atp/Modelfile` or `atp/generate_training_data.py`
2. Rebuild model:
   ```bash
   cd /mnt/d/demoproject/atp
   /mnt/c/Users/demouser/AppData/Local/Programs/Ollama/ollama.exe create atp-chatbot -f Modelfile
   ```
3. Restart app:
   ```bash
   docker-compose -f docker-compose-port5000-secure.yml restart web
   ```

### Database Changes
1. Edit `models.py`
2. Create migration:
   ```bash
   docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py makemigrations
   ```
3. Apply migration:
   ```bash
   docker-compose -f docker-compose-port5000-secure.yml exec web python manage.py migrate
   ```

---

## File Locations

| Component | Location |
|-----------|----------|
| Django Settings | `atp/atp/settings_secure.py` |
| URL Routing | `atp/atp/urls.py` |
| Stock Check Views | `atp/stockcheck/views.py` |
| Chatbot Views | `atp/chatbot/views.py` |
| Chatbot Services | `atp/chatbot/services/` |
| AI Model Definition | `atp/Modelfile` |
| Training Data Generator | `atp/generate_training_data.py` |
| Docker Config | `docker-compose-port5000-secure.yml` |
| Nginx Config | `nginx-fixed.conf` |

---

## Default Credentials (CHANGE IN PRODUCTION!)

### Application
- **Username**: admin
- **Password**: [REDACTED]

### Database
- **Root Password**: [REDACTED]
- **Django User**: dbuser
- **Django Password**: [REDACTED]

### SAP (Example - Update in settings)
- **User**: [REDACTED]
- **Password**: [REDACTED]

---

## Next Steps

1. **Read Full Documentation**: `DEVELOPER_GUIDE.md`
2. **Review Security**: Change all default passwords!
3. **Test SAP Connection**: Try product search
4. **Test AI Chat**: Verify context awareness
5. **Review Code**: Understand the architecture

---

## Support

- **Full Documentation**: See `DEVELOPER_GUIDE.md`
- **Training Data Info**: See `TRAINING_DATA_VERIFICATION.md`
- **Custom Model Guide**: See `CUSTOM_MODEL_TRAINING_GUIDE.md`

---

**Happy Coding! 🚀**
