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


class ContactMessage(models.Model):
    """مدل برای ذخیره پیام‌های تماس با ما"""
    STATUS_CHOICES = [
        ('new', 'جدید'),
        ('read', 'خوانده شده'),
        ('replied', 'پاسخ داده شده'),
        ('archived', 'بایگانی شده'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="نام و نام خانوادگی")
    email = models.EmailField(verbose_name="ایمیل")
    phone = models.CharField(max_length=20, verbose_name="شماره تماس", blank=True)
    subject = models.CharField(max_length=200, verbose_name="موضوع پیام")
    message = models.TextField(verbose_name="متن پیام")
    reply = models.TextField(
        verbose_name="پاسخ ادمین",
        blank=True,
        help_text="پاسخ به پیام کاربر"
    )
    replied_by = models.ForeignKey(
        'account.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_replies',
        verbose_name="پاسخ دهنده"
    )
    replied_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ پاسخ"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="وضعیت"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ارسال")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ به‌روزرسانی")
    admin_note = models.TextField(
        verbose_name="یادداشت ادمین",
        blank=True,
        help_text="یادداشت داخلی برای پیگیری"
    )
    
    class Meta:
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.subject}"
    
    def mark_as_read(self):
        """علامت‌گذاری به عنوان خوانده شده"""
        if self.status == 'new':
            self.status = 'read'
            self.save()


class StudentTeacherMessage(models.Model):
    """مدل برای پیام‌های زبان‌آموز به معلم"""
    student = models.ForeignKey(
        'account.Student',
        on_delete=models.CASCADE,
        related_name='messages_to_teacher',
        verbose_name="زبان‌آموز"
    )
    teacher = models.ForeignKey(
        'account.Teacher',
        on_delete=models.CASCADE,
        related_name='messages_from_students',
        verbose_name="معلم"
    )
    course = models.ForeignKey(
        'course.Course',
        on_delete=models.CASCADE,
        related_name='student_messages',
        verbose_name="دوره"
    )
    subject = models.CharField(max_length=200, verbose_name="موضوع")
    message = models.TextField(verbose_name="پیام")
    is_read = models.BooleanField(default=False, verbose_name="خوانده شده")
    teacher_reply = models.TextField(blank=True, verbose_name="پاسخ معلم")
    replied_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ پاسخ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ارسال")
    
    class Meta:
        verbose_name = "پیام زبان‌آموز به معلم"
        verbose_name_plural = "پیام‌های زبان‌آموز به معلم"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} به {self.teacher.user.get_full_name()} - {self.subject}"


class PrivateClassRequest(models.Model):
    """مدل برای ذخیره درخواست‌های کلاس خصوصی"""
    STATUS_CHOICES = [
        ('pending', 'در انتظار بررسی'),
        ('contacted', 'تماس گرفته شده'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
    ]
    
    LEVEL_CHOICES = [
        ('beginner', 'مبتدی'),
        ('intermediate', 'متوسط'),
        ('advanced', 'پیشرفته'),
        ('unknown', 'نمی‌دانم'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="نام و نام خانوادگی")
    email = models.EmailField(verbose_name="ایمیل")
    phone = models.CharField(max_length=20, verbose_name="شماره تماس")
    current_level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        verbose_name="سطح فعلی زبان",
        default='unknown'
    )
    preferred_time = models.CharField(
        max_length=100,
        verbose_name="زمان ترجیحی برگزاری کلاس",
        blank=True,
        help_text="مثال: عصرها، آخر هفته‌ها"
    )
    goals = models.TextField(
        verbose_name="اهداف و نیازهای شما",
        help_text="لطفاً اهداف خود از یادگیری زبان را توضیح دهید"
    )
    additional_info = models.TextField(
        verbose_name="توضیحات تکمیلی",
        blank=True,
        help_text="هر اطلاعات اضافی که می‌خواهید با ما در میان بگذارید"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="وضعیت"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ارسال")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ به‌روزرسانی")
    admin_note = models.TextField(
        verbose_name="یادداشت ادمین",
        blank=True,
        help_text="یادداشت داخلی برای پیگیری"
    )
    
    class Meta:
        verbose_name = "درخواست کلاس خصوصی"
        verbose_name_plural = "درخواست‌های کلاس خصوصی"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_current_level_display()}"



class CalendarEvent(models.Model):
    """مدل برای رویدادهای تقویم"""
    EVENT_TYPE_CHOICES = [
        ('class', 'کلاس'),
        ('assignment', 'تکلیف'),
        ('exam', 'امتحان'),
        ('meeting', 'جلسه'),
        ('holiday', 'تعطیلی'),
        ('reminder', 'یادآوری'),
        ('other', 'سایر'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'برنامه‌ریزی شده'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'تکمیل شده'),
        ('cancelled', 'لغو شده'),
    ]
    
    COLOR_CHOICES = [
        ('#4CAF50', 'سبز'),
        ('#2196F3', 'آبی'),
        ('#FF9800', 'نارنجی'),
        ('#F44336', 'قرمز'),
        ('#9C27B0', 'بنفش'),
        ('#00BCD4', 'فیروزه‌ای'),
        ('#FFC107', 'زرد'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="عنوان رویداد")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        default='other',
        verbose_name="نوع رویداد"
    )
    
    # زمان‌بندی
    start_datetime = models.DateTimeField(verbose_name="تاریخ و ساعت شروع")
    end_datetime = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ و ساعت پایان")
    all_day = models.BooleanField(default=False, verbose_name="تمام روز")
    
    # ارتباطات
    course = models.ForeignKey(
        'course.Course',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='calendar_events',
        verbose_name="دوره مرتبط"
    )
    assignment = models.ForeignKey(
        'course.Assignment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='calendar_events',
        verbose_name="تکلیف مرتبط"
    )
    
    # کاربران مرتبط
    created_by = models.ForeignKey(
        'account.User',
        on_delete=models.CASCADE,
        related_name='created_events',
        verbose_name="ایجاد کننده"
    )
    participants = models.ManyToManyField(
        'account.User',
        blank=True,
        related_name='calendar_events',
        verbose_name="شرکت‌کنندگان"
    )
    
    # تنظیمات ظاهری
    color = models.CharField(
        max_length=7,
        choices=COLOR_CHOICES,
        default='#2196F3',
        verbose_name="رنگ"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name="وضعیت"
    )
    
    # یادآوری
    reminder_minutes = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="یادآوری (دقیقه قبل)",
        help_text="چند دقیقه قبل از شروع یادآوری فعال شود"
    )
    
    # سایر
    location = models.CharField(max_length=200, blank=True, verbose_name="محل برگزاری")
    notes = models.TextField(blank=True, verbose_name="یادداشت‌ها")
    is_recurring = models.BooleanField(default=False, verbose_name="تکرارشونده")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    
    class Meta:
        verbose_name = "رویداد تقویم"
        verbose_name_plural = "رویدادهای تقویم"
        ordering = ['start_datetime']
        indexes = [
            models.Index(fields=['start_datetime']),
            models.Index(fields=['event_type']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_event_type_display()}"
    
    def is_past(self):
        """آیا رویداد گذشته است"""
        from django.utils import timezone
        return timezone.now() > (self.end_datetime or self.start_datetime)
    
    def duration_minutes(self):
        """مدت زمان رویداد به دقیقه"""
        if self.end_datetime:
            delta = self.end_datetime - self.start_datetime
            return int(delta.total_seconds() / 60)
        return 0
