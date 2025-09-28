from django.db import models
from django.utils import timezone
from django.utils.html import mark_safe
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

class FAQ(models.Model):
    question = models.CharField("سوال", max_length=300, help_text="سوال متداول کاربران")
    answer = models.TextField("پاسخ", help_text="پاسخ کامل و واضح به سوال")
    order = models.IntegerField("ترتیب", default=0, help_text="عدد کمتر = نمایش بالاتر")
    is_active = models.BooleanField("نمایش داده شود؟", default=True) # type: ignore
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "سوال متداول"
        verbose_name_plural = "سوالات متداول"
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.question


class HeroSlider(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان اصلی", help_text="عنوان بزرگ اسلایدر")
    subtitle = models.TextField(verbose_name="زیرعنوان", help_text="توضیحات کوتاه زیر عنوان", blank=True)
    image = models.ImageField(upload_to='hero_slides/', verbose_name="تصویر پس‌زمینه", 
                             help_text="اندازه پیشنهادی: ۱۹۲۰×۸۰۰ پیکسل", blank=True, null=True)
    button_text = models.CharField(max_length=50, verbose_name="متن دکمه", blank=True, help_text="مثل: مشاهده دوره‌ها")
    button_url = models.CharField(max_length=200, verbose_name="لینک دکمه", blank=True, help_text="آدرس صفحه‌ای که دکمه به آن می‌رود")
    order = models.IntegerField("ترتیب نمایش", default=0, help_text="عدد کمتر = نمایش زودتر")
    is_active = models.BooleanField("فعال", default=True, help_text="اسلایدر نمایش داده شود؟")
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "اسلایدر صفحه اصلی"
        verbose_name_plural = "اسلایدرهای صفحه اصلی"
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام شخص", help_text="نام دانش‌آموز یا معلم")
    role = models.CharField(max_length=100, verbose_name="سمت/نقش", help_text="مثل: دانش‌آموز دوره مکالمه")
    content = models.TextField(verbose_name="متن نظر", help_text="نظر و تجربه شخص")
    image = models.ImageField(upload_to='testimonials/', verbose_name="عکس شخص", 
                             help_text="اندازه پیشنهادی: ۲۰۰×۲۰۰ پیکسل", blank=True, null=True)
    rating = models.IntegerField(verbose_name="امتیاز", default=5, 
                                help_text="امتیاز از ۱ تا ۵ ستاره",
                                choices=[(i, f"{i} ستاره") for i in range(1, 6)])
    is_featured = models.BooleanField("ویژه", default=False, help_text="در صفحه اصلی نمایش داده شود؟")
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "نظر کاربران"
        verbose_name_plural = "نظرات کاربران"
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return f"{self.name} - {self.rating} ستاره"


class CourseGuide(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان", help_text="عنوان راهنمای دوره")
    description = models.TextField(verbose_name="توضیحات", blank=True, help_text="توضیح کوتاه درباره راهنما")
    image = models.ImageField(upload_to='course_guides/', verbose_name="تصویر", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "راهنمای دوره"
        verbose_name_plural = "راهنمای دوره‌ها"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CourseGuideItem(models.Model):
    guide = models.ForeignKey(CourseGuide, on_delete=models.CASCADE, related_name='items', verbose_name="راهنما")
    text = models.CharField("متن راهنما", max_length=300, help_text="نکته یا راهنمای مفید برای دانش‌آموزان")
    order = models.PositiveIntegerField("ترتیب نمایش", default=0) # type: ignore
    is_active = models.BooleanField("نمایش داده شود؟", default=True) # type: ignore
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "آیتم راهنما"
        verbose_name_plural = "آیتم‌های راهنما"
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.guide.title} - {self.text[:50]}" # type: ignore


class CompanyInfo(models.Model):
    """اطلاعات کلی شرکت که در سراسر سایت استفاده می‌شود"""
    company_name = models.CharField(max_length=100, verbose_name="نام آکادمی", 
                                   default="آکادمی زبان انگلیسی", 
                                   help_text="نام رسمی آکادمی")
    slogan = models.CharField(max_length=200, verbose_name="شعار", 
                             help_text="جمله کوتاه و جذاب درباره آکادمی", default='زبان')
    logo = models.ImageField(upload_to='company/', verbose_name="لوگو", 
                            help_text="اندازه پیشنهادی: ۲۰۰×۱۰۰ پیکسل", blank=True, null=True)
    favicon = models.ImageField(upload_to='company/', verbose_name="فاویکون", 
                               help_text="آیکون کوچک سایت - اندازه: ۳۲×۳۲ پیکسل", blank=True, null=True)
    
    # اطلاعات تماس اصلی
    main_phone = models.CharField(max_length=20, verbose_name="تلفن اصلی", 
                                 help_text="شماره تماس اصلی آکادمی")
    main_email = models.EmailField(verbose_name="ایمیل اصلی", 
                                  help_text="آدرس ایمیل رسمی آکادمی")
    address = models.TextField(verbose_name="آدرس", 
                              help_text="آدرس کامل آکادمی")
    
    # ساعات کاری
    working_hours = models.CharField(max_length=100, verbose_name="ساعات کاری", 
                                    default="شنبه تا پنج‌شنبه ۸ الی ۲۰", 
                                    help_text="ساعات کاری آکادمی")
    
    # متن کپی‌رایت
    copyright_text = models.CharField(max_length=200, verbose_name="متن کپی‌رایت", 
                                     default="تمامی حقوق محفوظ است", 
                                     help_text="متن کپی‌رایت در پایین سایت")
    
    # درباره ما خلاصه
    about_summary = models.TextField(verbose_name="خلاصه درباره ما", 
                                    help_text="متن کوتاه درباره آکادمی برای فوتر", 
                                    max_length=300)
    
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        verbose_name = "اطلاعات آکادمی"
        verbose_name_plural = "اطلاعات آکادمی"

    def __str__(self):
        return self.company_name

    def save(self, *args, **kwargs):
        # فقط یک رکورد مجاز
        if not self.pk and CompanyInfo.objects.exists():
            raise ValidationError('فقط یک رکورد اطلاعات آکادمی مجاز است')
        super().save(*args, **kwargs)


class FooterSection(models.Model):
    SECTION_CHOICES = [
        ('brand', 'برند'),
        ('quick_links', 'دسترسی سریع'),
        ('services', 'خدمات'),
        ('contact', 'تماس'),
    ]
    
    title = models.CharField(max_length=100, verbose_name="عنوان بخش")
    section_type = models.CharField(max_length=20, choices=SECTION_CHOICES, verbose_name="نوع بخش")
    order = models.IntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "بخش فوتر"
        verbose_name_plural = "بخش‌های فوتر"
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class FooterLink(models.Model):
    section = models.ForeignKey(FooterSection, on_delete=models.CASCADE, related_name='links', verbose_name="بخش")
    title = models.CharField(max_length=100, verbose_name="عنوان")
    url = models.CharField(max_length=200, verbose_name="لینک")
    icon = models.CharField(max_length=50, blank=True, verbose_name="آیکون")
    order = models.IntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "لینک فوتر"
        verbose_name_plural = "لینک‌های فوتر"
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class SocialMedia(models.Model):
    PLATFORM_CHOICES = [
        ('instagram', 'اینستاگرام'),
        ('telegram', 'تلگرام'),
        ('whatsapp', 'واتساپ'),
        ('youtube', 'یوتیوب'),
        ('facebook', 'فیسبوک'),
    ]
    
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, verbose_name="پلتفرم")
    url = models.URLField(verbose_name="لینک")
    icon = models.CharField(max_length=50, verbose_name="آیکون", blank=True)
    order = models.IntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    def save(self, *args, **kwargs):
        # Set default icon based on platform if not provided
        if not self.icon:
            icon_mapping = {
                'instagram': 'custom-icon instagram-icon',
                'telegram': 'custom-icon telegram-icon',
                'whatsapp': 'custom-icon whatsapp-icon',
                'youtube': 'custom-icon youtube-icon',
                'facebook': 'custom-icon facebook-icon',
            }
            self.icon = icon_mapping.get(self.platform, 'fas fa-link')
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "شبکه اجتماعی"
        verbose_name_plural = "شبکه‌های اجتماعی"
        ordering = ['order', 'platform']

    def __str__(self):
        return self.get_platform_display()


class ContactInfo(models.Model):
    CONTACT_TYPE_CHOICES = [
        ('address', 'آدرس'),
        ('phone', 'تلفن'),
        ('mobile', 'موبایل'),
        ('email', 'ایمیل'),
        ('fax', 'فکس'),
    ]
    
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES, verbose_name="نوع تماس")
    title = models.CharField(max_length=100, verbose_name="عنوان")
    value = models.CharField(max_length=200, verbose_name="مقدار")
    icon = models.CharField(max_length=50, verbose_name="آیکون")
    order = models.IntegerField(default=0, verbose_name="ترتیب")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "اطلاعات تماس"
        verbose_name_plural = "اطلاعات تماس"
        ordering = ['order', 'contact_type']

    def __str__(self):
        return f"{self.get_contact_type_display()}: {self.value}"


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, verbose_name="نام سایت")
    site_description = models.TextField(verbose_name="توضیحات سایت", blank=True)
    logo = models.ImageField(upload_to='site/', verbose_name="لوگو", blank=True, null=True)
    footer_description = models.TextField(verbose_name="توضیحات فوتر", blank=True)
    copyright_text = models.CharField(max_length=200, verbose_name="متن کپی‌رایت", blank=True)
    newsletter_title = models.CharField(max_length=100, verbose_name="عنوان خبرنامه", blank=True)
    newsletter_description = models.TextField(verbose_name="توضیحات خبرنامه", blank=True)

    developer_name = models.CharField(max_length=100, default='پارسا پرویزی')
    developer_text = models.CharField(max_length=150, default='تهیه شده توسط پارسا پرویزی')
    developer_link = models.URLField(blank=True)
    
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return self.site_name
    
    def get_developer_link(self):
        """Get developer link with fallback to settings default"""
        from django.conf import settings
        if self.developer_link:
            return self.developer_link
        return getattr(settings, 'EXTERNAL_URLS', {}).get('GITHUB_DEVELOPER', '')

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            return
        super().save(*args, **kwargs)


# class Log(models.Model):
#     LEVEL_CHOICES = [
#         ('info', 'Info'),
#         ('warning', 'Warning'),
#         ('error', 'Error'),
#         ('critical', 'Critical'),
#     ]
#     message = models.TextField()
#     level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
#     created_at = models.DateTimeField(auto_now_add=True)
#     user = models.ForeignKey('account.User', null=True, blank=True, on_delete=models.SET_NULL)
#     def __str__(self):
#         return f"{self.level}: {self.message[:50]}"


class AdviceRequest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "درخواست مشاوره"
        verbose_name_plural = "درخواست‌های مشاوره"


    def __str__(self):
        return f"{self.name} - {self.email}"


class DeterminationRequest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "درخواست تعیین سطح"
        verbose_name_plural = "درخواست‌های تعیین سطح"

    def __str__(self):
        return f"{self.name} - {self.email}"


def validate_pdf_file(value):
    """اعتبارسنجی فایل PDF"""
    if not value.name.lower().endswith('.pdf'):
        raise ValidationError('فقط فایل‌های PDF مجاز هستند.')
    
    # بررسی حجم فایل (حداکثر 5 مگابایت)
    if value.size > 5 * 1024 * 1024:
        raise ValidationError('حجم فایل نباید بیشتر از 5 مگابایت باشد.')

class CollabrateRequest(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام و نام خانوادگی")
    email = models.EmailField(verbose_name="آدرس ایمیل")
    phone = models.CharField(max_length=20, verbose_name="شماره تماس")
    message = models.TextField(verbose_name="پیام و توضیحات")
    resume = models.FileField(
        upload_to='resumes/',
        verbose_name="رزومه (PDF)",
        help_text="فایل رزومه خود را به فرمت PDF آپلود کنید (حداکثر 5 مگابایت)",
        validators=[validate_pdf_file],
        blank=True,
        null=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ارسال")
    STATUS_CHOICES = [
        ("pending", "در انتظار بررسی"),
        ("approved", "تایید شده"),
        ("rejected", "رد شده"),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="وضعیت درخواست"
    )
    class Meta:
        verbose_name = "درخواست همکاری"
        verbose_name_plural = "درخواست‌های همکاری"

    def __str__(self):
        return f"{self.name} - {self.email}"


class RequestCourse(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام درخواست‌دهنده")
    email = models.EmailField(verbose_name="ایمیل")
    phone = models.CharField(max_length=20, verbose_name="شماره تماس", blank=True)
    course_title = models.CharField(max_length=200, verbose_name="عنوان دوره پیشنهادی")
    description = models.TextField(verbose_name="توضیحات تکمیلی", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت درخواست")

    class Meta:
        verbose_name = "درخواست دوره"
        verbose_name_plural = "درخواست‌های دوره"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.course_title} - {self.name}"

