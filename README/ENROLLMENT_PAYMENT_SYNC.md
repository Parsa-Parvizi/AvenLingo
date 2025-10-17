# همگام‌سازی خودکار ثبت‌نام و پرداخت

## 📋 خلاصه
این سیستم اطمینان می‌دهد که وضعیت ثبت‌نام و پرداخت همیشه هماهنگ هستند و هیچ ثبت‌نام تأیید شده‌ای بدون پرداخت وجود ندارد (به جز دوره‌های رایگان).

## 🎯 قوانین اصلی

### برای دوره‌های غیر رایگان:
1. ✅ **ثبت‌نام `confirmed` = پرداخت `paid` یا `partial`**
2. ❌ **ثبت‌نام `confirmed` ≠ پرداخت `unpaid`**
3. 🔄 اگر پرداخت تأیید شود، ثبت‌نام خودکار تأیید می‌شود
4. 🔄 اگر ثبت‌نام بدون پرداخت تأیید شود، به `pending` برمی‌گردد

### برای دوره‌های رایگان:
1. ✅ **ثبت‌نام `confirmed` = پرداخت `paid` (خودکار)**
2. 💰 **مبلغ پرداختی = 0 تومان**
3. 🎁 نیازی به فرآیند پرداخت نیست

## 🔧 پیاده‌سازی

### 1. مدل `Enrollment`

#### متد `_sync_enrollment_payment_status()`
این متد در `save()` فراخوانی می‌شود و وضعیت‌ها را خودکار همگام می‌کند:

```python
def _sync_enrollment_payment_status(self):
    # دوره رایگان → payment = paid
    if self.course.is_free:
        self.payment_status = 'paid'
        self.amount_paid = 0
        return
    
    # دوره پولی:
    # confirmed بدون payment → pending
    if self.status == 'confirmed':
        if self.payment_status not in ['paid', 'partial']:
            self.status = 'pending'
            self.confirmed_at = None
    
    # payment موجود + pending → confirmed
    if self.payment_status in ['paid', 'partial'] and self.status == 'pending':
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
```

#### متد `confirm_enrollment()`
تأیید ایمن ثبت‌نام:

```python
success, message = enrollment.confirm_enrollment()

# بازگشت:
# (True, "ثبت‌نام با موفقیت تأیید شد") → موفق
# (False, "ابتدا باید پرداخت تأیید شود") → ناموفق
```

**مثال:**
```python
# دوره رایگان
enrollment.confirm_enrollment()  # ✅ همیشه موفق

# دوره پولی
enrollment.payment_status = 'unpaid'
enrollment.confirm_enrollment()  # ❌ "ابتدا باید پرداخت تأیید شود"

enrollment.payment_status = 'paid'
enrollment.confirm_enrollment()  # ✅ موفق
```

#### متد `confirm_payment()`
تأیید پرداخت و خودکار تأیید ثبت‌نام:

```python
success, message = enrollment.confirm_payment(amount=1000000)

# اگر ثبت‌نام pending بود، خودکار confirmed می‌شود
```

**مثال:**
```python
# دوره پولی pending
enrollment = Enrollment.objects.create(
    student=student,
    course=paid_course,
    status='pending',
    payment_status='unpaid'
)

# تأیید پرداخت
enrollment.confirm_payment(amount=paid_course.price)

# نتیجه:
# enrollment.status = 'confirmed' ✅
# enrollment.payment_status = 'paid' ✅
# enrollment.confirmed_at = timezone.now() ✅
```

#### متد `clean()`
اعتبارسنجی در سطح مدل:

```python
# در admin یا form ها
enrollment.clean()  # ValidationError اگر ناهماهنگ باشد
```

### 2. Admin Panel

#### فرم سفارشی
```python
class EnrollmentAdminForm(forms.ModelForm):
    def clean(self):
        # بررسی هماهنگی ثبت‌نام و پرداخت
        if not course.is_free:
            if status == 'confirmed' and payment_status not in ['paid', 'partial']:
                raise ValidationError("ابتدا باید پرداخت تأیید شود")
```

#### Action تأیید گروهی
```python
# انتخاب چند ثبت‌نام → Actions → "تأیید ثبت‌نام‌های انتخاب شده"
# فقط ثبت‌نام‌هایی با پرداخت تأیید شده، confirm می‌شوند
```

**خروجی نمونه:**
```
✅ 5 ثبت‌نام با موفقیت تأیید شد.
⚠️ 2 ثبت‌نام تأیید نشد: علی احمدی (ابتدا باید پرداخت تأیید شود), فاطمه محمدی (ابتدا باید پرداخت تأیید شود)
```

### 3. Management Command

دستور برای بررسی و اصلاح ثبت‌نام‌های ناهماهنگ:

```bash
# فقط نمایش مشکلات (بدون تغییر)
python manage.py sync_enrollment_payment --dry-run

# اصلاح خودکار مشکلات
python manage.py sync_enrollment_payment --fix
```

**خروجی نمونه:**
```
🔍 در حال بررسی ثبت‌نام‌ها...

✅ ID: 170 - جعفر حاجی نژاد → مکالمه تجاری - سطح ۴
   مشکل: ثبت‌نام تایید شده ولی پرداخت نشده
   وضعیت ثبت‌نام: در انتظار تأیید ← اصلاح شد
   وضعیت پرداخت: پرداخت نشده
   نوع دوره: غیر رایگان

======================================================================
⚠️  تعداد مشکلات یافت شده: 6
✅ تعداد اصلاح شده: 6
======================================================================
```

## 📊 سناریوهای مختلف

### سناریو 1: ثبت‌نام عادی در دوره پولی

```python
# 1. دانش‌آموز ثبت‌نام می‌کند
enrollment = Enrollment.objects.create(
    student=student,
    course=paid_course,
    status='pending',
    payment_status='unpaid'
)
# وضعیت: pending, پرداخت: unpaid ✅

# 2. دانش‌آموز فیش واریزی آپلود می‌کند
enrollment.payment_receipt = uploaded_file
enrollment.save()

# 3. ادمین پرداخت را تأیید می‌کند
enrollment.confirm_payment(amount=paid_course.price)
# وضعیت: confirmed ✅, پرداخت: paid ✅

# یا ادمین به صورت دستی تایید می‌کند:
enrollment.payment_status = 'paid'
enrollment.save()  # خودکار confirmed می‌شود ✅
```

### سناریو 2: ثبت‌نام در دوره رایگان

```python
# ثبت‌نام
enrollment = Enrollment.objects.create(
    student=student,
    course=free_course,
    status='confirmed'  # می‌تواند مستقیم confirmed باشد
)

# سیستم خودکار:
# enrollment.payment_status = 'paid' ✅
# enrollment.amount_paid = 0 ✅
```

### سناریو 3: پرداخت جزئی

```python
# ثبت‌نام
enrollment = Enrollment.objects.create(
    student=student,
    course=paid_course,
    status='pending',
    payment_status='unpaid'
)

# پرداخت بخشی از مبلغ
enrollment.payment_status = 'partial'
enrollment.amount_paid = paid_course.price / 2
enrollment.save()

# خودکار confirmed می‌شود ✅
enrollment.refresh_from_db()
assert enrollment.status == 'confirmed'
```

### سناریو 4: لغو پرداخت بعد از تأیید

```python
# ثبت‌نام تأیید شده
enrollment = Enrollment.objects.create(
    student=student,
    course=paid_course,
    status='confirmed',
    payment_status='paid'
)

# لغو پرداخت (مثلاً برگشت وجه)
enrollment.payment_status = 'refunded'
enrollment.save()

# خودکار به pending برمی‌گردد ✅
enrollment.refresh_from_db()
assert enrollment.status == 'pending'
assert enrollment.confirmed_at is None
```

### سناریو 5: سعی در تقلب (دور زدن سیستم)

```python
# تلاش برای تأیید بدون پرداخت
enrollment = Enrollment.objects.create(
    student=student,
    course=paid_course,
    status='confirmed',  # عمداً confirmed
    payment_status='unpaid'  # بدون پرداخت
)

# سیستم خودکار جلوگیری می‌کند ✅
enrollment.refresh_from_db()
assert enrollment.status == 'pending'  # برگشت به pending
```

## 🔒 امنیت

### محافظت‌های موجود:

1. **سطح مدل**: `_sync_enrollment_payment_status()` در هر `save()`
2. **سطح فرم**: `clean()` method در `EnrollmentAdminForm`
3. **سطح منطق**: `confirm_enrollment()` و `confirm_payment()` methods
4. **سطح دیتابیس**: بررسی‌های منظم با management command

### تضمین‌ها:

- ✅ هیچ ثبت‌نام `confirmed` بدون پرداخت وجود ندارد (دوره پولی)
- ✅ دوره‌های رایگان همیشه `paid` هستند
- ✅ پرداخت `partial` برای تأیید کافی است
- ✅ لغو پرداخت، ثبت‌نام را لغو می‌کند

## 📈 نظارت و نگهداری

### بررسی منظم:
```bash
# هفتگی یا ماهانه
python manage.py sync_enrollment_payment --dry-run

# اگر مشکلی وجود داشت:
python manage.py sync_enrollment_payment --fix
```

### لاگ‌گیری:
همه تغییرات در `EnrollmentHistory` ثبت می‌شود:
```python
EnrollmentHistory.objects.filter(enrollment=enrollment)
```

### آمار:
```python
from enrollment.models import Enrollment

# ثبت‌نام‌های تأیید شده
confirmed = Enrollment.objects.filter(status='confirmed').count()

# پرداخت‌های تأیید شده
paid = Enrollment.objects.filter(payment_status='paid').count()

# بررسی ناهماهنگی
inconsistent = Enrollment.objects.filter(
    status='confirmed',
    course__is_free=False
).exclude(payment_status__in=['paid', 'partial']).count()

print(f"ناهماهنگی: {inconsistent}")  # باید 0 باشد
```

## 🧪 تست‌ها

### تست‌های موجود:
- `test_free_course_auto_paid`: دوره رایگان خودکار paid می‌شود
- `test_paid_course_cannot_confirm_without_payment`: دوره پولی بدون پرداخت confirmed نمی‌شود
- `test_paid_course_can_confirm_with_full_payment`: پرداخت کامل → confirmed
- `test_paid_course_can_confirm_with_partial_payment`: پرداخت جزئی → confirmed
- `test_confirm_enrollment_method_*`: تست methodهای تأیید
- `test_confirm_payment_method`: تست تأیید پرداخت
- `test_clean_method_validation`: تست اعتبارسنجی
- `test_change_payment_after_confirm`: تغییر پرداخت بعد از تأیید
- `test_refunded_payment_status`: وضعیت refunded

### اجرای تست‌ها:
```bash
python manage.py test enrollment.test_enrollment_payment_sync
```

## 💡 نکات مهم

1. **پرداخت جزئی مجاز است**: دانش‌آموزان می‌توانند بخشی از مبلغ را پرداخت کرده و ثبت‌نام‌شان تأیید شود.

2. **دوره‌های رایگان**: نیازی به فرآیند پرداخت ندارند، خودکار `paid` می‌شوند.

3. **عدم تغییر گذشته**: این سیستم فقط از این به بعد اعمال می‌شود و ثبت‌نام‌های قبلی را تغییر نمی‌دهد (مگر با management command).

4. **سازگاری با کد موجود**: همه کدهای قبلی بدون تغییر کار می‌کنند.

5. **عملکرد**: `_sync_enrollment_payment_status()` بسیار سبک است و بر عملکرد تأثیری ندارد.

## 🔄 مهاجرت داده‌ها

برای همگام‌سازی ثبت‌نام‌های موجود:

```bash
# 1. ابتدا بررسی کنید
python manage.py sync_enrollment_payment --dry-run

# 2. اگر مشکلی وجود داشت، بررسی دستی کنید
# 3. سپس اصلاح کنید
python manage.py sync_enrollment_payment --fix

# 4. دوباره بررسی کنید
python manage.py sync_enrollment_payment
# باید پیام "✅ همه ثبت‌نام‌ها هماهنگ هستند!" را ببینید
```

## 🎓 مثال کامل

```python
from enrollment.models import Enrollment
from course.models import Course
from account.models import Student

# دریافت دوره و دانش‌آموز
course = Course.objects.get(id=1)
student = Student.objects.get(id=1)

# ثبت‌نام جدید
enrollment = Enrollment.objects.create(
    student=student,
    course=course,
    status='pending',
    payment_status='unpaid'
)

print(f"وضعیت: {enrollment.get_status_display()}")
print(f"پرداخت: {enrollment.get_payment_status_display()}")

# بررسی امکان تأیید
success, message = enrollment.confirm_enrollment()
print(message)  # "ابتدا باید پرداخت تأیید شود (حداقل بخشی از مبلغ)"

# تأیید پرداخت
success, message = enrollment.confirm_payment(amount=course.price)
print(message)  # "پرداخت تأیید شد و ثبت‌نام فعال گردید"

# بررسی نهایی
enrollment.refresh_from_db()
print(f"وضعیت نهایی: {enrollment.get_status_display()}")  # "تأیید شده"
print(f"پرداخت نهایی: {enrollment.get_payment_status_display()}")  # "پرداخت شده"
```

## 📞 پشتیبانی

اگر سوالی دارید یا مشکلی مشاهده کردید:

1. ابتدا `sync_enrollment_payment --dry-run` را اجرا کنید
2. لاگ‌های Django را بررسی کنید
3. جدول `EnrollmentHistory` را چک کنید
4. از Django shell برای بررسی دستی استفاده کنید

---

**تاریخ ایجاد**: ۱۷ اکتبر ۲۰۲۵  
**نسخه**: 1.0  
**وضعیت**: ✅ فعال و تست شده

