from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.sessions.models import Session

User = get_user_model()


class LoginHistory(models.Model):
    """تاریخچه ورود کاربران"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history', verbose_name='کاربر')
    login_time = models.DateTimeField('زمان ورود', default=timezone.now)
    logout_time = models.DateTimeField('زمان خروج', null=True, blank=True)
    ip_address = models.GenericIPAddressField('آدرس IP', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)
    device_type = models.CharField('نوع دستگاه', max_length=50, blank=True)  # desktop, mobile, tablet
    browser = models.CharField('مرورگر', max_length=100, blank=True)
    location = models.CharField('موقعیت', max_length=255, blank=True)
    is_successful = models.BooleanField('ورود موفق', default=True)
    session_key = models.CharField('کلید نشست', max_length=40, blank=True)
    
    class Meta:
        verbose_name = 'تاریخچه ورود'
        verbose_name_plural = 'تاریخچه ورودها'
        ordering = ['-login_time']
        indexes = [
            models.Index(fields=['user', '-login_time']),
            models.Index(fields=['ip_address']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.login_time}"
    
    @property
    def duration(self):
        """محاسبه مدت زمان نشست"""
        if self.logout_time:
            return self.logout_time - self.login_time
        return timezone.now() - self.login_time
    
    @property
    def is_active(self):
        """آیا نشست هنوز فعال است"""
        return self.logout_time is None


class CourseRequest(models.Model):
    """درخواست دوره توسط کاربران"""
    STATUS_CHOICES = [
        ('pending', 'در انتظار بررسی'),
        ('reviewing', 'در حال بررسی'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_requests', verbose_name='کاربر')
    course_title = models.CharField('عنوان دوره', max_length=255)
    description = models.TextField('توضیحات', help_text='توضیحات دوره مورد نظر')
    category = models.CharField('دسته‌بندی', max_length=100, blank=True)
    level = models.CharField('سطح', max_length=50, blank=True)
    estimated_students = models.IntegerField('تعداد دانش‌آموز تخمینی', default=0)
    status = models.CharField('وضعیت', max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField('یادداشت مدیر', blank=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('تاریخ بروزرسانی', auto_now=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='reviewed_course_requests', verbose_name='بررسی شده توسط')
    reviewed_at = models.DateTimeField('تاریخ بررسی', null=True, blank=True)
    
    class Meta:
        verbose_name = 'درخواست دوره'
        verbose_name_plural = 'درخواست‌های دوره'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.course_title} - {self.user.get_full_name()}"


class ConsultationRequest(models.Model):
    """درخواست مشاوره"""
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('scheduled', 'زمان‌بندی شده'),
        ('completed', 'انجام شده'),
        ('cancelled', 'لغو شده'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consultation_requests', verbose_name='کاربر')
    subject = models.CharField('موضوع', max_length=255)
    description = models.TextField('توضیحات')
    preferred_date = models.DateField('تاریخ ترجیحی', null=True, blank=True)
    preferred_time = models.TimeField('ساعت ترجیحی', null=True, blank=True)
    phone = models.CharField('شماره تماس', max_length=20, blank=True)
    status = models.CharField('وضعیت', max_length=20, choices=STATUS_CHOICES, default='pending')
    scheduled_date = models.DateTimeField('تاریخ قرار', null=True, blank=True)
    consultant = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='consultations', verbose_name='مشاور')
    admin_note = models.TextField('یادداشت مدیر', blank=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('تاریخ بروزرسانی', auto_now=True)
    
    class Meta:
        verbose_name = 'درخواست مشاوره'
        verbose_name_plural = 'درخواست‌های مشاوره'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.subject} - {self.user.get_full_name()}"


class SecuritySettings(models.Model):
    """تنظیمات امنیتی سیستم"""
    # Password Policy
    min_password_length = models.IntegerField('حداقل طول رمز عبور', default=8)
    require_uppercase = models.BooleanField('نیاز به حروف بزرگ', default=True)
    require_lowercase = models.BooleanField('نیاز به حروف کوچک', default=True)
    require_numbers = models.BooleanField('نیاز به اعداد', default=True)
    require_special_chars = models.BooleanField('نیاز به کاراکترهای خاص', default=False)
    password_expiry_days = models.IntegerField('انقضای رمز عبور (روز)', default=0, 
                                              help_text='0 = هیچوقت منقضی نمی‌شود')
    
    # Session Settings
    session_timeout_minutes = models.IntegerField('زمان انقضای نشست (دقیقه)', default=60)
    max_concurrent_sessions = models.IntegerField('حداکثر نشست همزمان', default=3)
    
    # Login Settings
    max_login_attempts = models.IntegerField('حداکثر تلاش ورود ناموفق', default=5)
    lockout_duration_minutes = models.IntegerField('مدت قفل شدن (دقیقه)', default=30)
    
    # Two-Factor Authentication
    enable_2fa = models.BooleanField('فعال‌سازی احراز هویت دو مرحله‌ای', default=False)
    force_2fa_for_admins = models.BooleanField('اجباری برای مدیران', default=False)
    
    # Other
    enable_email_verification = models.BooleanField('فعال‌سازی تایید ایمیل', default=True)
    log_failed_attempts = models.BooleanField('ثبت تلاش‌های ناموفق', default=True)
    
    updated_at = models.DateTimeField('آخرین بروزرسانی', auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='بروز شده توسط')
    
    class Meta:
        verbose_name = 'تنظیمات امنیتی'
        verbose_name_plural = 'تنظیمات امنیتی'
    
    def __str__(self):
        return f"تنظیمات امنیتی - {self.updated_at}"
    
    @classmethod
    def get_settings(cls):
        """دریافت یا ایجاد تنظیمات"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
