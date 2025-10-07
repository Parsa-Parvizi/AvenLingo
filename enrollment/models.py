from django.db import models
from django.utils import timezone
from datetime import timedelta
from account.models import Student
from course.models import Course


class Enrollment(models.Model):
    """Enhanced enrollment model with better tracking capabilities"""
    
    ENROLLMENT_STATUS_CHOICES = [
        ('pending', 'در انتظار تأیید'),
        ('confirmed', 'تأیید شده'),
        ('cancelled', 'لغو شده'),
        ('completed', 'تکمیل شده'),
        ('expired', 'منقضی شده'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('unpaid', 'پرداخت نشده'),
        ('paid', 'پرداخت شده'),
        ('partial', 'پرداخت جزئی'),
        ('refunded', 'عودت وجه'),
    ]

    # Core relationships
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')

    # Status tracking
    status = models.CharField(
        "وضعیت ثبت‌نام", 
        max_length=20, 
        choices=ENROLLMENT_STATUS_CHOICES, 
        default='pending'
    )
    payment_status = models.CharField(
        "وضعیت پرداخت",
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='unpaid'
    )

    # Timestamps
    enrolled_at = models.DateTimeField("زمان ثبت‌نام", auto_now_add=True)
    confirmed_at = models.DateTimeField("زمان تأیید", null=True, blank=True)
    cancelled_at = models.DateTimeField("زمان لغو", null=True, blank=True)
    
    # Additional information
    note = models.TextField("یادداشت", blank=True, help_text="یادداشت‌های اضافی در مورد ثبت‌نام")
    admin_note = models.TextField("یادداشت مدیریت", blank=True, help_text="یادداشت برای مدیران")
    
    # Payment tracking
    amount_paid = models.DecimalField("مبلغ پرداخت شده", max_digits=10, decimal_places=0, default=0)
    discount_applied = models.DecimalField("تخفیف اعمال شده", max_digits=10, decimal_places=0, default=0)
    payment_receipt = models.ImageField("فیش واریزی", upload_to='payment_receipts/', null=True, blank=True)
    
    # Enrollment source tracking
    enrollment_source = models.CharField(
        "منبع ثبت‌نام",
        max_length=50,
        choices=[
            ('website', 'وب‌سایت'),
            ('phone', 'تماس تلفنی'),
            ('referral', 'معرفی'),
            ('social_media', 'شبکه‌های اجتماعی'),
            ('other', 'سایر'),
        ],
        default='website'
    )
    
    # Progress tracking
    completion_percentage = models.PositiveIntegerField("درصد تکمیل", default=0)
    last_activity = models.DateTimeField("آخرین فعالیت", auto_now=True)

    class Meta:
        unique_together = ('student', 'course')
        verbose_name = "ثبت‌نام"
        verbose_name_plural = "ثبت‌نام‌ها"
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
            models.Index(fields=['enrolled_at']),
        ]

    def __str__(self):
        return f"{self.student} → {self.course} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-set confirmed_at when status changes to confirmed
        if self.status == 'confirmed' and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        
        # Auto-set cancelled_at when status changes to cancelled
        if self.status == 'cancelled' and not self.cancelled_at:
            self.cancelled_at = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Update course enrollment count
        self.update_course_enrollment_count()
    
    def update_course_enrollment_count(self):
        """Update the course's enrolled_count"""
        confirmed_count = self.course.enrollments.filter(status='confirmed').count()
        self.course.enrolled_count = confirmed_count
        self.course.save(update_fields=['enrolled_count'])
    
    @property
    def is_active(self):
        """Check if enrollment is active"""
        return self.status in ['confirmed', 'pending']
    
    @property
    def is_overdue_payment(self):
        """Check if payment is overdue (more than 7 days since enrollment)"""
        if self.payment_status == 'paid':
            return False
        return timezone.now() > self.enrolled_at + timedelta(days=7)
    
    @property
    def remaining_amount(self):
        """Calculate remaining amount to be paid"""
        total_amount = self.course.price - self.discount_applied
        return max(0, total_amount - self.amount_paid)
    
    @property
    def can_be_cancelled(self):
        """Check if enrollment can be cancelled"""
        return self.status in ['pending', 'confirmed'] and not self.is_course_started
    
    @property
    def is_course_started(self):
        """Check if the course has started"""
        return self.course.start_date <= timezone.now().date()
    
    def confirm_enrollment(self, confirmed_by=None):
        """Confirm the enrollment"""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.confirmed_at = timezone.now()
            self.save()
            return True
        return False
    
    def cancel_enrollment(self, reason="", cancelled_by=None):
        """Cancel the enrollment"""
        if self.can_be_cancelled:
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            if reason:
                self.admin_note = f"{self.admin_note}\nلغو شده: {reason}" if self.admin_note else f"لغو شده: {reason}"
            self.save()
            return True
        return False


class EnrollmentHistory(models.Model):
    """Track enrollment status changes for audit purposes"""
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='history')
    old_status = models.CharField("وضعیت قبلی", max_length=20)
    new_status = models.CharField("وضعیت جدید", max_length=20)
    changed_by = models.CharField("تغییر توسط", max_length=100, null=True, blank=True)
    changed_at = models.DateTimeField("زمان تغییر", auto_now_add=True)
    reason = models.TextField("دلیل تغییر", blank=True)
    
    class Meta:
        verbose_name = "تاریخچه ثبت‌نام"
        verbose_name_plural = "تاریخچه ثبت‌نام‌ها"
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.enrollment} - {self.old_status} → {self.new_status}"