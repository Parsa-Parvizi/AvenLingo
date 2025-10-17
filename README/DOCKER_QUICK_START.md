# 🚀 Docker Quick Start Guide

راهنمای سریع برای شروع کار با Docker در 5 دقیقه!

---

## ⚡ Development (راه‌اندازی سریع)

### گام 1: کپی فایل محیطی

```bash
cp env.development.template docker.env
```

### گام 2: اجرا!

```bash
# روش 1: استفاده از اسکریپت (پیشنهادی)
./docker-dev.sh

# روش 2: دستی
docker-compose up --build
```

### گام 3: دسترسی به برنامه

```bash
# برنامه
http://localhost:8000

# Admin panel
http://localhost:8000/admin
# Username: admin@academy.com
# Password: admin123
```

✅ **تمام!** برنامه شما آماده است.

---

## 🏭 Production Deployment

### پیش‌نیاز

```bash
# نصب Docker و Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### گام 1: تنظیمات محیطی

```bash
# کپی template
cp env.production.template .env.production

# ویرایش و تغییر مقادیر
nano .env.production
```

**حتماً تغییر بدید:**
- `DJANGO_SECRET_KEY` → کلید random 50+ کاراکتری
- `POSTGRES_PASSWORD` → رمز قوی 20+ کاراکتری
- `DJANGO_ALLOWED_HOSTS` → domain واقعی شما

### گام 2: Validation

```bash
./docker-validate.sh
```

### گام 3: Deploy!

```bash
# Build
./docker-build.sh

# Deploy
./docker-deploy.sh
```

✅ **Done!** برنامه شما در production در حال اجرا است.

### گام 4: بررسی

```bash
# وضعیت containers
docker-compose -f docker-compose.prod.yml ps

# مشاهده logs
docker-compose -f docker-compose.prod.yml logs -f

# بررسی سلامت
curl http://localhost/health/
```

---

## 📝 دستورات مهم

### Development

```bash
# شروع
docker-compose up -d

# توقف
docker-compose down

# Logs
docker-compose logs -f

# Shell در container
docker-compose exec web bash

# Django commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic
```

### Production

```bash
# شروع
docker-compose -f docker-compose.prod.yml up -d

# توقف
docker-compose -f docker-compose.prod.yml down

# Logs
docker-compose -f docker-compose.prod.yml logs -f

# Backup دیتابیس
docker-compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U englishteacher_user englishteacher_db \
  > backup_$(date +%Y%m%d).sql

# Update کردن
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 🔧 Troubleshooting

### مشکل: Container می‌میره

```bash
# بررسی logs
docker-compose logs web

# شروع مجدد
docker-compose restart web
```

### مشکل: Database connection error

```bash
# بررسی database
docker-compose ps db

# Restart database
docker-compose restart db
```

### مشکل: Port گرفته شده

```bash
# تغییر port در docker.env
DJANGO_PORT=8001
HTTP_PORT=8080
```

### مشکل: حجم زیاد

```bash
# پاکسازی
docker system prune -a --volumes

# حذف images قدیمی
docker image prune -a
```

---

## 📚 مستندات بیشتر

- **راهنمای کامل:** [DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md)
- **چک‌لیست:** [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- **بهینه‌سازی‌ها:** [DOCKER_OPTIMIZATION_SUMMARY.md](DOCKER_OPTIMIZATION_SUMMARY.md)

---

## 🆘 نیاز به کمک؟

1. بررسی کنید: [DOCKER_DEPLOYMENT_GUIDE.md](DOCKER_DEPLOYMENT_GUIDE.md#troubleshooting)
2. Logs را چک کنید: `docker-compose logs`
3. Configuration را validate کنید: `./docker-validate.sh`

---

**Happy Deployment! 🎉**

