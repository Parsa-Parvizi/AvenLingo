from django.db import models
from django.core.exceptions import ValidationError


def validate_pdf_file(value):
    """اعتبارسنجی فایل PDF"""
    if not value.name.lower().endswith('.pdf'):
        raise ValidationError('فقط فایل‌های PDF مجاز هستند.')
    
    # بررسی حجم فایل (حداکثر 5 مگابایت)
    if value.size > 5 * 1024 * 1024:
        raise ValidationError('حجم فایل نباید بیشتر از 5 مگابایت باشد.')


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

