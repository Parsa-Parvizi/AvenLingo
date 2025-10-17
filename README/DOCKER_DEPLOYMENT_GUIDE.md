# 🐳 راهنمای کامل Docker Deployment

این مستند راهنمای جامع برای deploy کردن پروژه English Teacher Academy با Docker است.

## 📋 فهرست مطالب

- [پیش‌نیازها](#پیش‌نیازها)
- [ساختار فایل‌های Docker](#ساختار-فایل‌های-docker)
- [Development Environment](#development-environment)
- [Production Deployment](#production-deployment)
- [بهینه‌سازی‌ها](#بهینه‌سازی‌ها)
- [نکات امنیتی](#نکات-امنیتی)
- [Troubleshooting](#troubleshooting)

---

## 🔧 پیش‌نیازها

### نصب Docker و Docker Compose

```bash
# بررسی نصب Docker
docker --version
docker-compose --version

# اگر نصب نیست:
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# نصب Docker Compose
sudo apt-get install docker-compose-plugin
```

### حداقل سیستم مورد نیاز

**Development:**
- RAM: 2GB
- CPU: 2 Cores
- Disk: 5GB

**Production:**
- RAM: 4GB (توصیه: 8GB)
- CPU: 2 Cores (توصیه: 4 Cores)
- Disk: 20GB (توصیه: 50GB)

---

## 📁 ساختار فایل‌های Docker

```
.
├── Dockerfile                      # Multi-stage Dockerfile (dev + production)
├── docker-compose.yml              # Development configuration
├── docker-compose.prod.yml         # Production configuration
├── .dockerignore                   # Files to exclude from Docker build
├── docker.env                      # Development environment variables
├── env.production.template         # Production environment template
├── env.development.template        # Development environment template
├── docker-build.sh                 # Build script
├── docker-deploy.sh                # Deployment script
├── docker-dev.sh                   # Quick dev start script
└── setup/
    └── entrypoint.sh               # Container entrypoint script
```

---

## 🛠️ Development Environment

### راه‌اندازی سریع

```bash
# 1. اجرای اسکریپت dev
./docker-dev.sh

# یا به صورت دستی:
docker-compose up --build
```

### گام به گام

#### 1. ایجاد فایل محیطی

```bash
# کپی کردن template
cp env.development.template docker.env

# ویرایش فایل (در صورت نیاز)
nano docker.env
```

#### 2. Build کردن images

```bash
# Build با cache
docker-compose build

# Build بدون cache (در صورت مشکل)
docker-compose build --no-cache
```

#### 3. اجرای سرویس‌ها

```bash
# اجرا در background
docker-compose up -d

# اجرا با نمایش logs
docker-compose up

# اجرای سرویس‌های خاص
docker-compose up db web
```

#### 4. مشاهده logs

```bash
# تمام سرویس‌ها
docker-compose logs -f

# سرویس خاص
docker-compose logs -f web
docker-compose logs -f db
```

#### 5. دستورات مفید

```bash
# دسترسی به shell در container
docker-compose exec web bash

# اجرای migration
docker-compose exec web python manage.py migrate

# ایجاد superuser
docker-compose exec web python manage.py createsuperuser

# جمع‌آوری static files
docker-compose exec web python manage.py collectstatic --noinput

# Django shell
docker-compose exec web python manage.py shell
```

#### 6. توقف سرویس‌ها

```bash
# توقف سرویس‌ها (حفظ volumes)
docker-compose stop

# توقف و حذف containers
docker-compose down

# حذف همه چیز (containers + volumes + networks)
docker-compose down -v
```

### Hot Reload در Development

در docker-compose.yml، کد شما به عنوان volume mount شده:

```yaml
volumes:
  - .:/app
```

این یعنی هر تغییری که در کد بدید، بلافاصله در container اعمال میشه.

---

## 🚀 Production Deployment

### آماده‌سازی

#### 1. ایجاد فایل محیطی Production

```bash
# کپی کردن template
cp env.production.template .env.production

# ویرایش با مقادیر واقعی
nano .env.production
```

#### 2. تنظیمات ضروری در `.env.production`

```bash
# ⚠️ حتماً تغییر بدید
DJANGO_SECRET_KEY=your-very-long-and-random-secret-key-at-least-50-characters
POSTGRES_PASSWORD=very-secure-random-password-minimum-20-chars
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,server-ip

# Email (اگر میخواید ایمیل ارسال کنید)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

#### 3. تولید Secret Key امن

```bash
# با Python
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# یا با OpenSSL
openssl rand -base64 48
```

### Deployment

#### روش 1: استفاده از اسکریپت (توصیه میشه)

```bash
# Build
./docker-build.sh

# Deploy
./docker-deploy.sh
```

#### روش 2: دستی

```bash
# 1. Build images
export DOCKER_BUILDKIT=1
docker-compose -f docker-compose.prod.yml build --parallel

# 2. Start database
docker-compose -f docker-compose.prod.yml up -d db

# 3. صبر کنید تا database آماده شود
sleep 10

# 4. Run migrations
docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate

# 5. Collect static files
docker-compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput

# 6. Start all services
docker-compose -f docker-compose.prod.yml up -d

# 7. بررسی وضعیت
docker-compose -f docker-compose.prod.yml ps
```

### بررسی سلامت سرویس‌ها

```bash
# وضعیت containers
docker-compose -f docker-compose.prod.yml ps

# Health check
docker-compose -f docker-compose.prod.yml exec web curl http://localhost:8000/health/

# Logs
docker-compose -f docker-compose.prod.yml logs -f

# منابع مصرفی
docker stats
```

### پشتیبان‌گیری

```bash
# Backup دیتابیس
mkdir -p backups
docker-compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U englishteacher_user englishteacher_db \
  > backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Restore دیتابیس
docker-compose -f docker-compose.prod.yml exec -T db \
  psql -U englishteacher_user englishteacher_db \
  < backups/backup_20241010_120000.sql
```

### به‌روزرسانی (Update)

```bash
# 1. Pull latest code
git pull origin main

# 2. Backup database
./docker-deploy.sh  # این script خودش backup میگیره

# یا manual:
# 3. Rebuild images
docker-compose -f docker-compose.prod.yml build

# 4. Restart services با zero-downtime
docker-compose -f docker-compose.prod.yml up -d --no-deps --build web

# 5. Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

---

## ⚡ بهینه‌سازی‌ها

### 1. Multi-Stage Build

Dockerfile ما از multi-stage build استفاده می‌کنه که باعث میشه:
- حجم image کمتر بشه (با حذف build dependencies)
- Build time کمتر بشه (با layer caching)
- Security بهتر بشه (فقط runtime dependencies)

### 2. Layer Caching

ترتیب لایه‌ها بهینه شده:
1. System dependencies (کمتر تغییر می‌کنه)
2. Python dependencies (گاهی تغییر می‌کنه)
3. Application code (بیشترین تغییر)

این باعث میشه rebuild ها خیلی سریع‌تر باشن.

### 3. .dockerignore

فایل `.dockerignore` بهینه شده و موارد غیرضروری رو exclude می‌کنه:
- `venv/` و `node_modules/`
- `.git/` و IDE files
- `logs/` و cache files
- Test files و documentation

### 4. حجم Image

```bash
# بررسی حجم
docker images englishteacher_web

# Expected size: ~300-400MB (بدون optional dependencies)
```

### 5. Dependencies بهینه شده

`requirements.txt` فقط شامل dependencies ضروری هست:
- ✅ Django core
- ✅ PostgreSQL driver
- ✅ Image processing
- ✅ Gunicorn
- ❌ Social auth (commented - اگر نیاز نیست)
- ❌ WeasyPrint (commented - اگر PDF نیاز نیست)

---

## 🔒 نکات امنیتی

### 1. Environment Variables

```bash
# ❌ هرگز commit نکنید:
.env
.env.production
.env.local

# ✅ فقط templates رو commit کنید
env.production.template
env.development.template
```

### 2. Secret Key

```bash
# ❌ استفاده نکنید:
SECRET_KEY=django-insecure-...
SECRET_KEY=dev-secret-key

# ✅ استفاده کنید:
SECRET_KEY=$(openssl rand -base64 48)
```

### 3. Database Password

```bash
# ❌ Weak passwords:
POSTGRES_PASSWORD=password123
POSTGRES_PASSWORD=admin

# ✅ Strong passwords:
POSTGRES_PASSWORD=$(openssl rand -base64 32)
```

### 4. ALLOWED_HOSTS

```python
# ❌ Never in production:
ALLOWED_HOSTS = ['*']

# ✅ Specific domains only:
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
```

### 5. Debug Mode

```bash
# Production:
DJANGO_DEBUG=False

# Development only:
DJANGO_DEBUG=True
```

### 6. SSL/HTTPS (اگر دارید)

```bash
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

## 🐛 Troubleshooting

### مشکل: Container بلافاصله بعد از start می‌میره

```bash
# بررسی logs
docker-compose logs web

# بررسی exit code
docker-compose ps
```

**راه‌حل‌های رایج:**
- بررسی syntax error در settings.py
- بررسی database connection
- بررسی environment variables

### مشکل: Database connection error

```bash
# بررسی که database running هست
docker-compose ps db

# بررسی health check
docker-compose exec db pg_isready -U englishteacher_user

# بررسی logs
docker-compose logs db
```

**راه‌حل:**
```bash
# Restart database
docker-compose restart db

# یا rebuild
docker-compose up -d --force-recreate db
```

### مشکل: Static files serve نمیشه

```bash
# Collect static files دوباره
docker-compose exec web python manage.py collectstatic --noinput --clear

# بررسی volume
docker volume ls
docker volume inspect englishteacher_static_volume
```

### مشکل: Port already in use

```bash
# پیدا کردن process که port رو استفاده می‌کنه
sudo lsof -i :8000
sudo lsof -i :80

# Kill کردن process
sudo kill -9 <PID>

# یا تغییر port در docker.env
DJANGO_PORT=8001
HTTP_PORT=8080
```

### مشکل: Out of disk space

```bash
# بررسی فضا
df -h

# حذف unused images
docker image prune -a

# حذف unused volumes
docker volume prune

# حذف همه چیز که استفاده نمیشه
docker system prune -a --volumes
```

### مشکل: Build بسیار کند است

```bash
# استفاده از BuildKit
export DOCKER_BUILDKIT=1

# بررسی .dockerignore
# اطمینان حاصل کنید که venv/, node_modules/ exclude شدن

# استفاده از cache
docker-compose build --build-arg BUILDKIT_INLINE_CACHE=1
```

### مشکل: Migration error

```bash
# بررسی که database آماده است
docker-compose exec db psql -U englishteacher_user -d englishteacher_db

# Fake migration (اگر لازم باشه)
docker-compose exec web python manage.py migrate --fake <app_name> <migration_name>

# Reset migrations (احتیاط کنید!)
docker-compose exec web python manage.py migrate <app_name> zero
docker-compose exec web python manage.py migrate
```

---

## 📊 Monitoring

### Resource Usage

```bash
# Real-time monitoring
docker stats

# Specific container
docker stats englishteacher_web_prod
```

### Logs Management

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100

# Specific service
docker-compose -f docker-compose.prod.yml logs -f web

# Save logs to file
docker-compose -f docker-compose.prod.yml logs > app-logs.txt
```

### Health Checks

```bash
# Manual health check
curl http://localhost/health/

# Container health status
docker inspect --format='{{.State.Health.Status}}' englishteacher_web_prod
```

---

## 🎯 Best Practices

### 1. Always Use `.env` Files
هرگز credentials رو hardcode نکنید.

### 2. Regular Backups
حداقل هفتگی از database backup بگیرید.

### 3. Monitor Resources
به طور مرتب منابع مصرفی رو چک کنید.

### 4. Update Dependencies
به طور منظم dependencies رو update کنید:

```bash
# بررسی outdated packages
docker-compose exec web pip list --outdated

# Update requirements.txt
# Rebuild image
docker-compose build --no-cache
```

### 5. Security Scans

```bash
# Scan image for vulnerabilities
docker scan englishteacher_web:latest

# یا با trivy
trivy image englishteacher_web:latest
```

### 6. Use Specific Image Tags
به جای `latest`، از version tags استفاده کنید.

---

## 📞 پشتیبانی

در صورت مشکل:
1. ابتدا [Troubleshooting](#troubleshooting) رو بررسی کنید
2. Logs رو چک کنید: `docker-compose logs`
3. Health checks رو بررسی کنید
4. Documentation Django رو مطالعه کنید

---

## 📝 Changelog

### v3.0 (Current)
- ✅ Multi-stage Docker build
- ✅ Optimized layer caching
- ✅ Minimal dependencies
- ✅ Separate dev/prod configurations
- ✅ Automated deployment scripts
- ✅ Enhanced security settings

---

**تاریخ آخرین به‌روزرسانی:** 2025-10-10

