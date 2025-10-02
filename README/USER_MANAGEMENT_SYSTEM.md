# سیستم مدیریت کاربران - آکادمی زبان مبینا

## معرفی

این سند توضیح کاملی از سیستم مدیریت کاربران بازسازی شده برای آکادمی زبان مبینا ارائه می‌دهد. سیستم جدید بر اساس بهترین روش‌های برنامه‌نویسی و اصول Domain-Driven Design طراحی شده است.

## انواع کاربران

### 1. دانش‌آموز (Student)
- ثبت‌نام مستقیم از طریق فرم ثبت‌نام
- نیاز به تایید ایمیل برای فعال‌سازی حساب
- دسترسی به دوره‌ها و امکانات آموزشی

### 2. مدرس (Teacher)
- **مرحله اول**: ارسال درخواست همکاری
- **مرحله دوم**: بررسی توسط ادمین
- **مرحله سوم**: در صورت تایید، ایجاد حساب کاربری

### 3. ادمین (Admin)
- مدیریت درخواست‌های همکاری معلمان
- نظارت بر سیستم و کاربران

## فرایند ثبت‌نام دانش‌آموز

```python
# 1. دانش‌آموز فرم ثبت‌نام را پر می‌کند
# 2. سیستم اعتبارسنجی انجام می‌دهد
# 3. کاربر ایجاد می‌شود (غیرفعال)
# 4. ایمیل تایید ارسال می‌شود
# 5. دانش‌آموز روی لینک کلیک می‌کند
# 6. حساب فعال می‌شود
```

### ویژگی‌های کلیدی:
- ✅ اعتبارسنجی قوی ایمیل و داده‌ها
- ✅ بررسی تکراری نبودن ایمیل
- ✅ تایید ایمیل با توکن امن
- ✅ انقضای لینک تایید پس از ۲۴ ساعت
- ✅ Rate limiting برای جلوگیری از سوءاستفاده

## فرایند درخواست همکاری معلم

```python
# 1. معلم فرم درخواست همکاری را پر می‌کند
# 2. سیستم اعتبارسنجی انجام می‌دهد
# 3. درخواست در دیتابیس ذخیره می‌شود
# 4. ایمیل اطلاع‌رسانی به ادمین ارسال می‌شود
# 5. ادمین درخواست را بررسی می‌کند
# 6. در صورت تایید:
#    - ایمیل تایید به معلم ارسال می‌شود
#    - لینک ثبت‌نام ۳۰ روز معتبر است
# 7. معلم حساب کاربری ایجاد می‌کند
```

### ویژگی‌های کلیدی:
- ✅ فرم جامع با اطلاعات حرفه‌ای
- ✅ آپلود فایل CV (PDF)
- ✅ سیستم تایید/رد با دلیل
- ✅ انقضای خودکار درخواست‌ها
- ✅ جلوگیری از درخواست تکراری

## ساختار کد

### 1. Models (مدل‌ها)
```python
# account/models.py

# User - مدل اصلی کاربر
class User(AbstractBaseUser, PermissionsMixin, UserStatusMixin):
    # اطلاعات اصلی، تایید ایمیل، وضعیت

# Student - پروفایل دانش‌آموز
class Student(ProfileCompletionMixin):
    # اطلاعات تحصیلی، اهداف، سطح زبان

# TeacherApplication - درخواست همکاری معلم
class TeacherApplication(models.Model):
    # اطلاعات حرفه‌ای، وضعیت بررسی

# Teacher - پروفایل معلم
class Teacher(ProfileCompletionMixin):
    # اطلاعات تدریس، ارتباط با درخواست
```

### 2. Services (خدمات)
```python
# account/services.py

# UserRegistrationService - مدیریت ثبت‌نام
class UserRegistrationService:
    @staticmethod
    def register_student(...)
    def register_teacher_from_application(...)
    def verify_student_email(...)

# TeacherApplicationService - مدیریت درخواست‌ها
class TeacherApplicationService:
    @staticmethod
    def submit_application(...)
    def approve_application(...)
    def reject_application(...)

# EmailService - مدیریت ایمیل‌ها
class EmailService:
    @staticmethod
    def send_student_verification_email(...)
    def send_teacher_approval_email(...)
```

### 3. Views (نماها)
```python
# account/views.py

# StudentRegistrationView - ثبت‌نام دانش‌آموز
# TeacherApplicationView - درخواست همکاری
# TeacherRegistrationView - ثبت‌نام معلم
# EmailVerificationView - تایید ایمیل
# TeacherApplicationApprovalView - تایید/رد درخواست
```

## امنیت

### اقدامات امنیتی:
1. **Rate Limiting**: محدودیت تعداد درخواست
2. **Token-based Verification**: تایید ایمیل با توکن امن
3. **Input Validation**: اعتبارسنجی قوی ورودی‌ها
4. **CSRF Protection**: حفاظت در برابر CSRF
5. **Logging**: ثبت تمام فعالیت‌های مهم
6. **File Upload Security**: بررسی امنیت فایل‌های آپلود شده

## دیتابیس

### جداول اصلی:
- `account_user`: کاربران اصلی
- `account_student`: پروفایل دانش‌آموزان
- `account_teacherapplication`: درخواست‌های همکاری
- `account_teacher`: پروفایل معلمان

### ایندکس‌ها:
```sql
-- بهینه‌سازی کارایی
CREATE INDEX idx_user_email_type ON account_user(email, user_type);
CREATE INDEX idx_user_status ON account_user(is_active, user_type);
CREATE INDEX idx_app_status_date ON account_teacherapplication(status, submitted_at);
```

## API Endpoints

### کاربران:
- `POST /auth/register/student/` - ثبت‌نام دانش‌آموز
- `POST /auth/verify-email/<user_id>/<token>/` - تایید ایمیل
- `GET /auth/dashboard/` - هدایت به داشبورد

### معلمان:
- `POST /auth/teacher/apply/` - درخواست همکاری
- `GET /auth/register/teacher/<email>/` - ثبت‌نام معلم
- `POST /auth/admin/applications/<id>/approve/` - تایید درخواست

### AJAX:
- `POST /auth/validate-email/` - بررسی موجود بودن ایمیل

## تنظیمات

### متغیرهای محیط:
```python
# settings.py
SITE_URL = 'https://academy.example.com'
SITE_NAME = 'آکادمی زبان مبینا'
DEFAULT_FROM_EMAIL = 'noreply@academy.com'

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

## Migration و نگهداری

### دستورات مفید:
```bash
# اعتبارسنجی سیستم
python manage.py migrate_teacher_system --validate-system

# پاک‌سازی درخواست‌های تکراری
python manage.py migrate_teacher_system --cleanup-duplicates

# برطرف کردن درخواست‌های منقضی
python manage.py migrate_teacher_system --fix-expired

# اجرای آزمایشی (بدون تغییر)
python manage.py migrate_teacher_system --dry-run --validate-system
```

## مانیتورینگ

### لاگ‌های مهم:
```python
# account.registration - ثبت‌نام‌ها
# account.login - ورود کاربران
# account.email_verification - تایید ایمیل
# account.teacher_application - درخواست‌های همکاری
```

### متریک‌های کلیدی:
- تعداد ثبت‌نام‌های روزانه
- نرخ تایید ایمیل
- تعداد درخواست‌های همکاری
- نرخ تایید معلمان

## تست

### تست‌های موجود:
```bash
# تست‌های یونیت
python manage.py test account.tests.test_models
python manage.py test account.tests.test_services
python manage.py test account.tests.test_views

# تست‌های یکپارچه
python manage.py test tests.test_integration
```

## بهبودهای آینده

### ویژگی‌های پیشنهادی:
1. **Two-Factor Authentication (2FA)**: احراز هویت دو مرحله‌ای
2. **Social Login**: ورود با شبکه‌های اجتماعی
3. **Advanced Analytics**: تحلیل رفتار کاربران
4. **Automated Teacher Verification**: تایید خودکار معلمان
5. **Mobile API**: API برای اپلیکیشن موبایل

## خطاهای رایج و راه‌حل

### 1. ایمیل تایید ارسال نمی‌شود
```python
# بررسی تنظیمات ایمیل
# چک کردن لاگ‌ها
# تست SMTP connection
```

### 2. درخواست معلم تکراری
```python
# استفاده از cleanup command
python manage.py migrate_teacher_system --cleanup-duplicates
```

### 3. لینک تایید منقضی شده
```python
# ارسال مجدد ایمیل از داشبورد
# یا استفاده از EmailService.send_student_verification_email()
```

## پشتیبانی

برای گزارش مشکلات یا درخواست ویژگی جدید:
- ایجاد Issue در مخزن پروژه
- تماس با تیم توسعه
- مراجعه به مستندات API

---

**نکته**: این سیستم مطابق با استانداردهای امنیتی و بهترین روش‌های Django طراحی شده است. 