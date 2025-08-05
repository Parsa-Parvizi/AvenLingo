from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

class ContactUs(models.Model):
    """اطلاعات تماس با ما - فقط یک رکورد مجاز"""
    
    # اطلاعات تماس اصلی
    phone = models.CharField(
        max_length=20, 
        verbose_name="تلفن ثابت",
        default='021-12345678',
        help_text="شماره تلفن ثابت آکادمی",
        validators=[RegexValidator(r'^[\d\-\+\(\)\s]+$', 'فرمت شماره تلفن صحیح نیست')]
    )
    
    mobile = models.CharField(
        max_length=15, 
        verbose_name="تلفن همراه",
        default='09123456789',
        help_text="شماره موبایل آکادمی",
        validators=[RegexValidator(r'^09\d{9}$', 'فرمت موبایل باید ۰۹ و ۱۱ رقم باشد')]
    )
    
    email = models.EmailField(
        verbose_name="ایمیل",
        default='info@academy.com',
        help_text="آدرس ایمیل رسمی آکادمی"
    )
    
    address = models.TextField(
        verbose_name="آدرس",
        default='تهران، خیابان ...',
        help_text="آدرس کامل آکادمی"
    )
    
    postal_code = models.CharField(
        max_length=10,
        verbose_name="کد پستی",
        blank=True,
        help_text="کد پستی ۱۰ رقمی",
        validators=[RegexValidator(r'^\d{10}$', 'کد پستی باید ۱۰ رقم باشد')]
    )
    
    # شبکه‌های اجتماعی
    instagram = models.URLField(
        blank=True, 
        verbose_name="اینستاگرام",
        default='https://instagram.com/academy',
        help_text="آدرس کامل صفحه اینستاگرام"
    )
    
    telegram = models.URLField(
        blank=True, 
        verbose_name="تلگرام",
        default='https://t.me/academy',
        help_text="آدرس کانال یا گروه تلگرام"
    )
    
    whatsapp = models.CharField(
        max_length=15,
        blank=True,
        verbose_name="واتساپ",
        default='09123456789',
        help_text="شماره واتساپ (بدون + و کد کشور)",
        validators=[RegexValidator(r'^09\d{9}$', 'فرمت موبایل واتساپ صحیح نیست')]
    )
    
    linkedin = models.URLField(
        blank=True, 
        verbose_name="لینکدین",
        default='https://linkedin.com/company/academy',
        help_text="آدرس صفحه لینکدین شرکت"
    )
    
    youtube = models.URLField(
        blank=True, 
        verbose_name="یوتیوب",
        default='https://youtube.com/@academy',
        help_text="آدرس کانال یوتیوب"
    )
    
    # ساعات کاری
    working_hours = models.TextField(
        verbose_name="ساعات کاری",
        default="شنبه تا پنج‌شنبه: ۸ صبح تا ۲۰\nجمعه: تعطیل",
        help_text="ساعات کاری آکادمی"
    )
    
    # نقشه
    map_embed_code = models.TextField(
        verbose_name="کد نقشه",
        blank=True,
        help_text="کد HTML نقشه گوگل مپس (iframe)"
    )
    
    # متادیتا
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        verbose_name = "اطلاعات تماس"
        verbose_name_plural = "اطلاعات تماس"

    def __str__(self):
        return "اطلاعات تماس آکادمی"
    
    def save(self, *args, **kwargs):
        # فقط یک رکورد مجاز
        if not self.pk and ContactUs.objects.exists():
            raise ValidationError('فقط یک رکورد اطلاعات تماس مجاز است')
        super().save(*args, **kwargs)
    
    @property
    def whatsapp_url(self):
        """لینک واتساپ برای استفاده در قالب"""
        if self.whatsapp:
            return f"https://wa.me/98{self.whatsapp[1:]}"  # حذف 0 و اضافه کردن کد کشور
        return ""


class AboutUs(models.Model):
    """صفحه درباره ما - فقط یک رکورد مجاز"""
    
    title = models.CharField(
        max_length=200, 
        verbose_name="عنوان صفحه",
        default='درباره آکادمی زبان انگلیسی',
        help_text="عنوان اصلی صفحه درباره ما"
    )
    
    subtitle = models.CharField(
        max_length=300,
        verbose_name="زیرعنوان",
        blank=True,
        help_text="جمله کوتاه زیر عنوان اصلی"
    )
    
    main_content = models.TextField(
        verbose_name="متن اصلی",
        help_text="متن کامل درباره آکادمی، تاریخچه، اهداف و ...",
        default='آکادمی زبان انگلیسی ما با سال‌ها تجربه در آموزش...'
    )
    
    mission = models.TextField(
        verbose_name="ماموریت ما",
        blank=True,
        help_text="ماموریت و هدف آکادمی"
    )
    
    vision = models.TextField(
        verbose_name="چشم‌انداز ما",
        blank=True,
        help_text="آینده‌نگری و اهداف بلندمدت"
    )
    
    values = models.TextField(
        verbose_name="ارزش‌های ما",
        blank=True,
        help_text="اصول و ارزش‌هایی که آکادمی بر آن‌ها استوار است"
    )
    
    # تصاویر
    main_image = models.ImageField(
        upload_to='about/',
        verbose_name="تصویر اصلی",
        blank=True, null=True,
        help_text="تصویر اصلی صفحه درباره ما - اندازه پیشنهادی: ۸۰۰×۴۰۰ پیکسل"
    )
    
    team_image = models.ImageField(
        upload_to='about/',
        verbose_name="تصویر تیم",
        blank=True, null=True,
        help_text="عکس تیم آکادمی - اندازه پیشنهادی: ۶۰۰×۴۰۰ پیکسل"
    )
    
    # آمار و ارقام
    students_count = models.PositiveIntegerField(
        verbose_name="تعداد دانش‌آموزان",
        default=0,
        help_text="تعداد کل دانش‌آموزان آکادمی"
    )
    
    teachers_count = models.PositiveIntegerField(
        verbose_name="تعداد اساتید",
        default=0,
        help_text="تعداد اساتید آکادمی"
    )
    
    courses_count = models.PositiveIntegerField(
        verbose_name="تعداد دوره‌ها",
        default=0,
        help_text="تعداد دوره‌های ارائه شده"
    )
    
    experience_years = models.PositiveIntegerField(
        verbose_name="سال‌های تجربه",
        default=1,
        help_text="سال‌های فعالیت آکادمی"
    )
    
    # SEO
    meta_description = models.CharField(
        max_length=160,
        verbose_name="توضیح SEO",
        blank=True,
        help_text="توضیح کوتاه برای موتورهای جستجو (حداکثر ۱۶۰ کاراکتر)"
    )
    
    # متادیتا
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        verbose_name = "درباره ما"
        verbose_name_plural = "درباره ما"

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # فقط یک رکورد مجاز
        if not self.pk and AboutUs.objects.exists():
            raise ValidationError('فقط یک صفحه درباره ما مجاز است')
        super().save(*args, **kwargs)


class ContactMessage(models.Model):
    """پیام‌های دریافتی از فرم تماس"""
    
    name = models.CharField(
        max_length=100,
        verbose_name="نام و نام خانوادگی"
    )
    
    email = models.EmailField(
        verbose_name="ایمیل"
    )
    
    phone = models.CharField(
        max_length=15,
        verbose_name="شماره تماس",
        blank=True,
        validators=[RegexValidator(r'^[\d\-\+\(\)\s]+$', 'فرمت شماره تلفن صحیح نیست')]
    )
    
    subject = models.CharField(
        max_length=200,
        verbose_name="موضوع"
    )
    
    message = models.TextField(
        verbose_name="پیام"
    )
    
    is_read = models.BooleanField(
        verbose_name="خوانده شده",
        default=False
    )
    
    is_replied = models.BooleanField(
        verbose_name="پاسخ داده شده",
        default=False
    )
    
    admin_notes = models.TextField(
        verbose_name="یادداشت ادمین",
        blank=True,
        help_text="یادداشت داخلی برای ادمین"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ارسال"
    )
    
    replied_at = models.DateTimeField(
        verbose_name="تاریخ پاسخ",
        null=True, blank=True
    )

    class Meta:
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"
