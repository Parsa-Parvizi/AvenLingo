# 🎓 English Teacher Academy - Mobina Garshasbi

## 📚 آکادمی زبان انگلیسی مبینا گرشاسبی (Django)
یک سیستم کامل مدیریت آکادمی زبان با امکانات ثبت‌نام دانش‌آموز/مدرس، دوره‌ها، ثبت‌نام‌ها، داشبورد نقش‌محور، و رابط کاربری مدرن و واکنش‌گرا.

---

## 🔗 لینک‌های سریع
- صفحه اصلی: `/`
- ورود/ثبت‌نام: `/auth/login/`، `/auth/register/student/`
- داشبوردها: `/auth/dashboard/` (هدایت خودکار به داشبورد نقش)
  - دانش‌آموز: `/auth/dashboard/student/`
  - مدرس: `/auth/dashboard/teacher/`
- اساتید: `/teachers/all-teachers/`
- جزئیات استاد: `/teachers/detail/<uuid:teacher_id>/`
- درخواست دوره: `/request-course/`
- ادمین: `/admin/`

---

## 🧭 فهرست مطالب
- [ویژگی‌ها](#-ویژگیها)
- [پیش‌نیازها](#-پیشنیازها)
- [راه‌اندازی سریع](#-راهاندازی-سریع)
  - [اجرای محلی](#-اجرای-محلی)
  - [Docker](#-docker)
- [پیکربندی](#-پیکربندی)
- [داده‌های نمونه](#-دادههای-نمونه)
- [احراز هویت و نقش‌ها](#-احراز-هویت-و-نقشها)
- [داشبوردها](#-داشبوردها)
- [اجرای تست‌ها](#-اجرای-تستها)
- [ساختار پروژه](#-ساختار-پروژه)
- [استقرار (Deployment)](#-استقرار-deployment)
- [امنیت و عملکرد](#-امنیت-و-عملکرد)
- [عیب‌یابی](#-عیبیابی)

---

## ✅ ویژگی‌ها

### 🔐 احراز هویت و کاربران
- احراز هویت سفارشی با ایمیل (ورود با ایمیل یا شماره موبایل)
- ثبت‌نام دانش‌آموز با پروفایل خودکار و تایید ایمیل
- ثبت‌نام مدرس فقط پس از تایید ادمین (فرآیند درخواست همکاری → تایید → ثبت‌نام)
- سیستم مدیریت کاربران بازطراحی شده با معماری Services Layer

### 🎨 رابط کاربری مدرن
- طراحی مدرن و واکنش‌گرا با استایل یکپارچه
- صفحه جزئیات استاد با Hero Section مدرن و نمایش دوره‌ها در Grid
- Toggle Switch مدرن برای "مرا به خاطر بسپار"
- آیکون نمایش/مخفی کردن رمز عبور در فرم‌های ورود و ثبت‌نام
- نمایش Inline و تمیز وضعیت‌های دوره (ویژه، رایگان، آنلاین/حضوری)

### ✨ اعتبارسنجی فرم‌ها
- اعتبارسنجی Real-time با بازخورد بصری (بردر سبز/قرمز)
- نشانگر قدرت رمز عبور با سه سطح:
  - 🔴 آسان (رد می‌شود)
  - 🟡 متوسط (8 کاراکتر + اعداد + حروف)
  - 🟢 قوی (8 کاراکتر + اعداد + حروف + کاراکترهای خاص)
- غیرفعال‌سازی دکمه ثبت‌نام/ورود تا پر شدن و اعتبارسنجی تمام فیلدهای الزامی
- بررسی Real-time موجود بودن ایمیل
- فیلدهای الزامی: نام، نام خانوادگی، ایمیل، شماره تلفن، رمز عبور
- Autocomplete off برای فیلدهای حساس

### 📚 مدیریت دوره‌ها و ثبت‌نام
- داشبورد نقش‌محور (دانش‌آموز/مدرس) با آمار و جداول
- مدیریت دوره‌ها، دسته‌بندی، ثبت‌نام‌ها، ظرفیت و وضعیت‌ها
- نمایش badge های دوره به صورت Inline و تمیز
- سیستم ثبت‌نام با بررسی ظرفیت و پیش‌نیازها

### 🚀 عملکرد و استقرار
- آماده استقرار با Docker و راهنمای VPS
- شاخص‌های دیتابیس و بهینه‌سازی Query ها
- Cache layer برای بهبود عملکرد
- Migration های بهینه‌شده و پاکسازی شده

---

## 🧰 پیش‌نیازها
- Python 3.10+
- PostgreSQL (یا SQLite برای توسعه)
- NodeJS (اختیاری برای ابزارهای فرانت)
- Docker و Docker Compose (اختیاری)

---

## 🚀 راه‌اندازی سریع

### 🖥️ اجرای محلی
```bash
# کلون و ورود به پروژه
git clone https://github.com/Parsa-Parvizi/MobinaGarshasbi.git
cd MobinaGarshasbi/

# نصب وابستگی‌ها
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# تنظیم متغیرها (نمونه)
export DEBUG=True
export SECRET_KEY=dev-secret
export DB_NAME=mydb
export DB_USER=myuser
export DB_PASSWORD=mypassword
export DB_HOST=localhost
export DB_PORT=5432

# اعمال مایگریشن‌ها و اجرای پروژه
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 🐳 Docker
```bash
git clone https://github.com/Parsa-Parvizi/MobinaGarshasbi.git
cd MobinaGarshasbi/

# اجرا
docker-compose up -d --build

# راه‌اندازی اولیه
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --noinput
```

---

## ⚙️ پیکربندی
فایل‌های مرتبط:
- تنظیمات جنگو: `EnglishTeacher/settings.py`
- تنظیمات تست: `EnglishTeacher/test_settings.py`
- متغیرهای محیطی مهم:
```env
DEBUG=True|False
SECRET_KEY=your-secure-key
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=...
DB_PORT=...
EMAIL_HOST=...
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
EMAIL_PORT=...
EMAIL_USE_TLS=...
```

---

## 🧪 داده‌های نمونه
فرمان seed برای ایجاد داده‌های نمایشی آماده است:
```bash
python manage.py seed_demo_data
```
(در صورت نیاز پرچم‌های اضافی را در کد فرمان بررسی کنید.)

---

## 🔐 احراز هویت و نقش‌ها
- مدل کاربر سفارشی: `account.User` با `USERNAME_FIELD = 'email'`
- ورود: «ایمیل یا شماره موبایل + رمز عبور» (موبایل به ایمیل کاربر نگاشت می‌شود)
- نقش‌ها: `student`، `teacher`، `admin`
- ثبت‌نام دانش‌آموز: پروفایل `Student` به‌صورت خودکار ایجاد می‌شود
- ثبت‌نام مدرس: تنها پس از تایید درخواست همکاری توسط ادمین (ایجاد `Teacher`)

### ویژگی‌های امنیتی فرم‌های ثبت‌نام و ورود
- **اعتبارسنجی Real-time**: بررسی فوری صحت ورودی‌ها با نمایش بصری (بردر سبز/قرمز)
- **نشانگر قدرت رمز**: سه سطح آسان/متوسط/قوی با الزامات مشخص
- **بررسی یکتایی ایمیل**: بررسی خودکار در دیتابیس
- **فیلدهای الزامی**: نام، نام خانوادگی، ایمیل، تلفن، رمز عبور
- **Autocomplete Off**: جلوگیری از پیشنهادات خودکار مرورگر
- **نمایش/مخفی رمز**: آیکون چشم برای کنترل نمایش رمز عبور

مسیرهای کلیدی:
- ورود: `/auth/login/`
- ثبت‌نام دانش‌آموز: `/auth/register/student/`
- ثبت‌نام مدرس (پس از تایید ایمیل دعوت): `/auth/register/teacher/<email>/`
- خروج: `/auth/logout/`

---

## 🗂️ داشبوردها
- مسیر هوشمند: `/auth/dashboard/` → بر اساس نقش هدایت می‌شود
- دانش‌آموز: `/auth/dashboard/student/`
  - ثبت‌نام‌ها، وضعیت‌ها، پیشرفت یادگیری، دوره‌های پیشنهادی
- مدرس: `/auth/dashboard/teacher/`
  - دوره‌های من، دانش‌آموزان اخیر، فعالیت‌ها، دسترسی سریع

صفحات مکمل بخش مدرس:
- لیست اساتید: `/teachers/all-teachers/`
- پروفایل مدرس (Hero Section مدرن): `/teachers/detail/<uuid:teacher_id>/`
- دوره‌های مدرس: `/teachers/courses/`
- دانش‌آموزان یک دوره: `/teachers/courses/<id>/students/`
- ایجاد دوره: `/teachers/create-course/`

---

## 🧑‍🔬 اجرای تست‌ها
```bash
# با تنظیمات تست
export DJANGO_SETTINGS_MODULE=EnglishTeacher.test_settings
pytest -q

# یا
python manage.py test
```
فولدرهای تست: `account/tests.py`، `course/tests.py`، `enrollment/tests.py`، `tests/` و غیره.

---

## 🏗️ ساختار پروژه
```
MobinaGarshasbi/
├── account/            # کاربران، فرم‌ها، ویوها، مدل‌های User/Student/TeacherApplication/Teacher
│   ├── services.py     # لایه سرویس برای منطق کسب‌وکار
│   └── management/     # دستورات مدیریتی (migrate_teacher_system)
├── core/               # تنظیمات سایت، صفحات استاتیک، دستورات مدیریت
│   └── management/commands/
│       ├── seed_fresh_data.py   # داده‌های نمونه تازه
│       ├── add_test_data.py     # داده‌های تست
│       └── clean_old_data.py    # پاکسازی داده‌های قدیمی
├── contact/            # تماس با ما و درباره ما
├── course/             # دوره‌ها، دسته‌بندی، وضعیت‌ها
├── teacher/            # بخش مدرس (ویوها و URLهای جداگانه)
├── enrollment/         # ثبت‌نام دانش‌آموزان در دوره‌ها
├── templates/          # قالب‌های HTML (یکپارچه با تم مدرن)
│   ├── account/
│   │   ├── emails/     # قالب‌های ایمیل (تایید، تأیید/رد مدرس)
│   │   ├── login.html  # فرم ورود با Toggle Switch و Password Toggle
│   │   └── student_register.html  # فرم ثبت‌نام با Validation پیشرفته
│   └── teacher/
│       └── teacher_detail.html    # صفحه جزئیات با Hero Section
├── static/             # CSS, JS, Images (طراحی مدرن و Responsive)
├── EnglishTeacher/     # تنظیمات پروژه جنگو
├── manage.py
└── requirements*.txt
```

---

## 🚀 استقرار (Deployment)
- بررسی راهنماها در `README/VPS_DEPLOYMENT_GUIDE.md` و `README/FINAL_DEPLOYMENT_CHECKLIST.md`
- راهنمای مدیریت کاربران: `README/USER_MANAGEMENT_SYSTEM.md`
- نکات مهم:
  - `DEBUG=False` و تنظیم `ALLOWED_HOSTS`
  - تنظیم ایمیل ارسال
  - جمع‌آوری استاتیک: `python manage.py collectstatic --noinput`
  - پایگاه‌داده: اجرای مایگریشن‌ها و پیکربندی بک‌آپ
  - اجرای دستور `seed_fresh_data` برای داده‌های اولیه

---

## 🛡️ امنیت و عملکرد
- تایید ایمیل برای فعال‌سازی حساب (پیکربندی ایمیل لازم است)
- محدودسازی تلاش‌های ورود و ثبت‌نام (Rate Limit)
- لاگینگ امنیتی برای ورود/خروج
- شاخص‌های دیتابیس و بهینه‌سازی‌های مدل‌ها
- استفاده از `X-Forwarded-For` در لاگ IP هنگام استقرار پشت پروکسی
- اعتبارسنجی Real-time و جلوگیری از ثبت‌نام با داده‌های نامعتبر
- Password strength validation با سه سطح امنیتی
- محافظت از فیلدهای حساس با Autocomplete Off

---

## 🆘 عیب‌یابی
1) مشکل import در تست‌ها:
```bash
export PYTHONPATH=$(pwd)
export DJANGO_SETTINGS_MODULE=EnglishTeacher.test_settings
pytest -q
```
2) عدم نمایش استایل‌ها در Production:
```bash
python manage.py collectstatic --noinput
```
3) عدم دسترسی مدرس به داشبورد:
- مطمئن شوید `Teacher` برای کاربر ایجاد و تایید شده است
- آدرس صحیح: `/auth/dashboard/teacher/`

---

## 🎉 شروع کنید!
```bash
python manage.py runserver
# یا
docker-compose up -d
```
اگر سوالی دارید از راهنماهای پوشه `README/` کمک بگیرید. موفق باشید! 🌟 