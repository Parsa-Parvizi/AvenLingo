# راهنمای سیستم Pagination کلاس‌ها

## خلاصه
سیستم pagination برای قسمت کلاس‌ها پیاده‌سازی شده است که در هر صفحه 21 کلاس نمایش داده می‌شود.

## ویژگی‌های پیاده‌سازی شده

### 1. منطق Pagination در Views
- **all_courses_view**: نمایش همه کلاس‌ها با pagination
- **featured_courses_view**: نمایش کلاس‌های ویژه با pagination  
- **category_courses_view**: نمایش کلاس‌های دسته‌بندی با pagination

### 2. کامپوننت Pagination قابل استفاده مجدد
- فایل: `templates/core/pagination.html`
- شامل دکمه‌های قبلی/بعدی
- نمایش شماره صفحات
- حفظ پارامترهای جستجو و فیلتر

### 3. طراحی Responsive
- سازگار با موبایل و تبلت
- انیمیشن‌های زیبا
- طراحی شبیه به بقیه سایت

## نحوه استفاده

### در Templates
```html
{% include 'core/pagination.html' with paginated_object=courses %}
```

### در Views
```python
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# پیاده‌سازی pagination
paginator = Paginator(courses, 21)  # 21 کلاس در هر صفحه
page = request.GET.get('page')

try:
    paginated_courses = paginator.page(page)
except PageNotAnInteger:
    paginated_courses = paginator.page(1)
except EmptyPage:
    paginated_courses = paginator.page(paginator.num_pages)
```

## URL Parameters
- `page`: شماره صفحه (مثال: `?page=2`)
- حفظ پارامترهای جستجو و فیلتر (مثال: `?search=english&page=2`)

## ویژگی‌های طراحی

### رنگ‌بندی
- استفاده از گرادیان آبی-بنفش مشابه سایت
- دکمه فعال: گرادیان رنگی
- دکمه غیرفعال: خاکستری

### انیمیشن‌ها
- Hover effects
- Transition animations
- Loading animations

### ریسپانسیو
- موبایل: دکمه‌های کوچکتر
- تبلت: اندازه متوسط
- دسکتاپ: اندازه کامل

## فایل‌های تغییر یافته

### Views
- `course/views.py`: اضافه شدن منطق pagination

### Templates
- `templates/core/pagination.html`: کامپوننت جدید
- `templates/course/all_courses.html`: اضافه شدن pagination
- `templates/course/featured_courses.html`: اضافه شدن pagination
- `templates/course/category_courses.html`: اضافه شدن pagination

## تست
سیستم pagination با 30 کلاس موجود تست شده و به درستی 2 صفحه تولید می‌کند (صفحه اول: 21 کلاس، صفحه دوم: 9 کلاس).

## نکات مهم
1. Pagination فقط زمانی نمایش داده می‌شود که بیش از یک صفحه وجود داشته باشد
2. پارامترهای جستجو و فیلتر در pagination حفظ می‌شوند
3. طراحی کاملاً responsive است
4. از استانداردهای accessibility پیروی می‌کند
