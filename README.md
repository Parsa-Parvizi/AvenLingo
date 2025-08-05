# 🎓 **English Teacher Academy - Mobina Garshasbi**

## 📚 **آکادمی زبان انگلیسی مبینا گرشاسبی**

یک سیستم مدیریت آکادمی زبان انگلیسی کامل و حرفه‌ای با Django

---

## 🚀 **شروع سریع**

### 📂 **ساختار پروژه**
```
MobinaGarshasbi/
├── account/            # مدیریت کاربران
├── core/               # عملکردهای اصلی
├── contact/            # تماس با ما و درباره ما
├── course/             # مدیریت دوره‌ها
├── teacher/            # مدیریت مدرسان
├── enrollment/         # ثبت‌نام دانش‌آموزان
├── templates/          # قالب‌های HTML
├── static/             # فایل‌های CSS, JS, Images
├── media/              # فایل‌های آپلود شده
├── EnglishTeacher/     # تنظیمات Django
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies
├── docker-compose.yml  # Docker configuration
├── DockerfileBack      # Docker build file
└── *.md               # مستندات راهنما
```

### 🔧 **نصب و راه‌اندازی**

#### **1. راه‌اندازی محلی**
```bash
# clone repository
git clone https://github.com/Parsa-Parvizi/MobinaGarshasbi.git
cd MobinaGarshasbi/

# نصب dependencies
pip install -r requirements.txt

# تنظیم environment variables
export DEBUG=True
export DB_NAME=mydb
export DB_USER=myuser  
export DB_PASSWORD=mypassword

# اجرای migrations
python manage.py migrate

# ایجاد superuser
python manage.py createsuperuser

# اجرای سرور
python manage.py runserver
```

#### **2. راه‌اندازی با Docker**
```bash
# clone repository
git clone https://github.com/Parsa-Parvizi/MobinaGarshasbi.git
cd MobinaGarshasbi/

# راه‌اندازی کامل با Docker
docker-compose up -d --build

# اجرای setup اولیه
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --noinput
```

---

## 🎯 **ویژگی‌های کلیدی**

### ✅ **مدیریت محتوای پیشرفته**
- 🏢 **اطلاعات آکادمی** - نام، لوگو، اطلاعات تماس
- 🎬 **اسلایدر صفحه اصلی** - تصاویر و متن‌های تبلیغاتی
- 💬 **نظرات کاربران** - testimonial با امتیازدهی
- ❓ **سوالات متداول** - FAQ با امکان مرتب‌سازی
- 📞 **اطلاعات تماس** - آدرس، تلفن، شبکه‌های اجتماعی

### ✅ **رابط ادمین حرفه‌ای**
- 🎨 **رابط فارسی** با راهنمایی کامل
- 🔐 **سطوح دسترسی** برای ادمین‌های مختلف
- 📝 **فرم‌های کاربرپسند** با validation
- 📊 **گزارش‌گیری** از پیام‌ها و درخواست‌ها

### ✅ **طراحی مدرن و Responsive**
- 🎨 **سیستم CSS یکپارچه** با متغیرهای جهانی
- 📱 **سازگار با موبایل** و تبلت
- 🖱️ **انیمیشن‌های نرم** برای hover و transition
- 🎭 **تم رنگی حرفه‌ای** بنفش و طلایی

### ✅ **آماده برای Production**
- 🐳 **Docker configuration** کامل
- 🔒 **تنظیمات امنیتی** پیشرفته
- 📧 **سیستم ایمیل** برای فرم تماس
- 💾 **پشتیبان‌گیری خودکار** از database
- 🚀 **راهنمای deployment** روی VPS

---

## 📚 **مستندات**

### 📖 **راهنماهای موجود**
- 🚀 **VPS_DEPLOYMENT_GUIDE.md** - راهنمای کامل نصب روی VPS
- 📋 **ADMIN_GUIDE.md** - راهنمای کاربری پنل ادمین
- 📊 **DEPLOYMENT_SUMMARY.md** - خلاصه تکنیکی پیاده‌سازی
- 📚 **STUDENT_APP_ANALYSIS.md** - تحلیل معماری برنامه
- ✅ **FINAL_DEPLOYMENT_CHECKLIST.md** - چک‌لیست نهایی

---

## 🎓 **نکات مهم**

### 🔑 **دسترسی ادمین**
- **URL**: `http://localhost:8000/admin/`
- **کاربری**: superuser که ایجاد کردید
- **زبان**: فارسی با راهنمایی کامل

### 📁 **مدیریت فایل‌ها**
- **Static Files**: CSS, JS, Images در `static/`
- **Media Files**: فایل‌های آپلود شده در `media/`
- **Templates**: قالب‌های HTML در `templates/`

### 🔧 **Environment Variables**
برای Production حتماً تنظیم کنید:
```env
DEBUG=False
SECRET_KEY=your-secure-key
ALLOWED_HOSTS=yourdomain.com
DB_NAME=production_db
DB_USER=production_user
DB_PASSWORD=secure_password
```

---

## 🆘 **راهنمایی و پشتیبانی**

### 🐛 **عیب‌یابی رایج**
1. **مشکل Database**: `python manage.py migrate`
2. **مشکل Static Files**: `python manage.py collectstatic`
3. **مشکل ادمین**: `python manage.py createsuperuser`

### 📞 **کسب اطلاعات بیشتر**
- مطالعه فایل‌های راهنما (*.md) در همین دایرکتوری
- بررسی `VPS_DEPLOYMENT_GUIDE.md` برای deployment
- مطالعه `ADMIN_GUIDE.md` برای مدیریت محتوا

---

## 🎉 **شروع کنید!**

```bash
python manage.py runserver
# یا
docker-compose up -d
```

**🚀 آکادمی شما آماده خدمت‌رسانی به دانش‌آموزان است!** 