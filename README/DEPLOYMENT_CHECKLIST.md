# ✅ چک‌لیست Deployment - English Teacher Academy

این چک‌لیست قبل از هر deployment باید کامل بررسی بشه.

## 📋 قبل از Deployment

### 1️⃣ محیط Development

- [ ] تمام تست‌ها pass شدن
- [ ] هیچ migration pending نمونده
- [ ] Static files به درستی جمع‌آوری میشن
- [ ] تمام features جدید تست شدن
- [ ] کد در Git commit شده

### 2️⃣ تنظیمات Docker

- [ ] `Dockerfile` بررسی شده
- [ ] `docker-compose.prod.yml` بررسی شده
- [ ] `.dockerignore` کامل هست
- [ ] `requirements.txt` فقط dependencies ضروری داره
- [ ] `setup/entrypoint.sh` قابل اجرا هست (`chmod +x`)

### 3️⃣ Environment Variables

- [ ] `.env.production` از template ساخته شده
- [ ] `DJANGO_SECRET_KEY` تغییر کرده (حداقل 50 کاراکتر)
- [ ] `POSTGRES_PASSWORD` قوی هست (حداقل 20 کاراکتر)
- [ ] `DJANGO_ALLOWED_HOSTS` با domain های واقعی تنظیم شده
- [ ] `DJANGO_DEBUG=False` تنظیم شده
- [ ] Email settings تنظیم شده (اگر نیاز هست)
- [ ] `.env.production` در `.gitignore` هست

### 4️⃣ امنیت

- [ ] Secret key بسیار قوی و random هست
- [ ] Database password قوی هست
- [ ] DEBUG mode خاموش هست (`False`)
- [ ] ALLOWED_HOSTS درست تنظیم شده (نه `*`)
- [ ] Rate limiting فعال هست
- [ ] فایل‌های محرمانه در `.dockerignore` هستن
- [ ] SSL/HTTPS (اگر دارید) تنظیم شده

### 5️⃣ Database

- [ ] PostgreSQL نصب و راه‌اندازی شده
- [ ] Backup strategy تعریف شده
- [ ] Connection settings درست هست
- [ ] Migration files موجود هستن

### 6️⃣ Static Files & Media

- [ ] Volume برای `staticfiles` تعریف شده
- [ ] Volume برای `media` تعریف شده
- [ ] Nginx برای serve کردن static files تنظیم شده
- [ ] مجوزهای فایل درست هست

---

## 🚀 حین Deployment

### مرحله 1: Validation

```bash
# اجرای validation script
./docker-validate.sh

# بررسی docker-compose config
docker-compose -f docker-compose.prod.yml config
```

- [ ] Validation بدون error گذشت
- [ ] Docker Compose config بدون مشکل هست

### مرحله 2: Backup

```bash
# Backup از database فعلی (اگر update هست)
mkdir -p backups
docker-compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U $POSTGRES_USER $POSTGRES_DB > backups/backup_$(date +%Y%m%d_%H%M%S).sql
```

- [ ] Backup database گرفته شد
- [ ] Backup در مکان امن ذخیره شد
- [ ] حجم backup معقول هست

### مرحله 3: Build

```bash
# Build images
export DOCKER_BUILDKIT=1
./docker-build.sh
```

- [ ] Build بدون error تمام شد
- [ ] حجم image معقول هست (< 500MB)
- [ ] Image tag گذاری شد

### مرحله 4: Deploy

```bash
# Deploy
./docker-deploy.sh
```

- [ ] Database service up شد
- [ ] Migrations اجرا شد
- [ ] Static files collect شد
- [ ] Web service up شد
- [ ] Nginx service up شد

### مرحله 5: Health Check

```bash
# بررسی health
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml exec web curl http://localhost:8000/health/
```

- [ ] تمام containers running هستن
- [ ] Health check pass شد
- [ ] No restart loops

---

## ✔️ بعد از Deployment

### بررسی فوری (اولین 5 دقیقه)

- [ ] صفحه اصلی لود میشه
- [ ] Login کار می‌کنه
- [ ] Static files serve میشن (CSS, JS, Images)
- [ ] Admin panel دسترسی داره
- [ ] Database queries کار می‌کنن
- [ ] هیچ 500 error نیست

### بررسی عمیق (اولین ساعت)

- [ ] ثبت‌نام کاربر جدید کار می‌کنه
- [ ] Upload فایل کار می‌کنه
- [ ] Email ارسال میشه (اگر تنظیم شده)
- [ ] فرم‌ها submit میشن
- [ ] Search کار می‌کنه
- [ ] Logs خطای critical نداره

### Monitoring

```bash
# Logs
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# Resource usage
docker stats

# Disk space
df -h
```

- [ ] CPU usage معقول هست (< 80%)
- [ ] Memory usage معقول هست (< 80%)
- [ ] Disk space کافی هست (> 20% free)
- [ ] No error logs
- [ ] Response time خوب هست (< 2s)

### Security Check

- [ ] Admin panel فقط با user/pass درست accessible هست
- [ ] Debug mode خاموش هست
- [ ] Error pages generic هستن (no stack traces)
- [ ] CSRF protection کار می‌کنه
- [ ] Rate limiting کار می‌کنه

---

## 🔄 Rollback Plan (اگر مشکل پیش اومد)

### روش 1: بازگشت به Image قبلی

```bash
# Stop current
docker-compose -f docker-compose.prod.yml down

# Use previous image tag
docker tag englishteacher_web:20241009-120000 englishteacher_web:latest

# Start
docker-compose -f docker-compose.prod.yml up -d
```

### روش 2: Restore Database

```bash
# Stop web service
docker-compose -f docker-compose.prod.yml stop web

# Restore database
docker-compose -f docker-compose.prod.yml exec -T db \
  psql -U $POSTGRES_USER $POSTGRES_DB < backups/backup_20241009_120000.sql

# Start web service
docker-compose -f docker-compose.prod.yml start web
```

---

## 📞 اطلاعات تماس اضطراری

در صورت مشکل:

1. بررسی logs: `docker-compose -f docker-compose.prod.yml logs`
2. بررسی [DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md)
3. اجرای rollback plan
4. تماس با تیم فنی

---

## 📝 یادداشت‌ها

```
تاریخ آخرین deployment: _____________
نسخه: _____________
Deploy شده توسط: _____________
مشکلات (اگر بود): _____________
_________________________________
_________________________________
```

---

**✅ تمام موارد بالا رو قبل از production deployment چک کنید!**

