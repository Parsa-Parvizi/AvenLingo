import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.mail import send_mail


class CustomUserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('آدرس ایمیل باید وارد شود')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_student(self, email, password, first_name, last_name, **extra_fields):
        """Create a student user"""
        extra_fields.setdefault('user_type', 'student')
        extra_fields.setdefault('is_active', True)
        extra_fields['first_name'] = first_name
        extra_fields['last_name'] = last_name
        
        return self.create_user(email, password, **extra_fields)
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model using email as unique identifier"""
    
    USER_TYPE_CHOICES = (
        ('student', 'دانش‌آموز'),
        ('teacher', 'مدرس'),
        ('admin', 'ادمین'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField('آدرس ایمیل', unique=True)
    first_name = models.CharField('نام', max_length=30, blank=True)
    last_name = models.CharField('نام خانوادگی', max_length=30, blank=True)
    user_type = models.CharField('نوع کاربر', max_length=10, choices=USER_TYPE_CHOICES, default='student')
    
    is_active = models.BooleanField('فعال', default=True)
    is_staff = models.BooleanField('کارمند', default=False)
    is_superuser = models.BooleanField('سوپر کاربر', default=False)
    
    date_joined = models.DateTimeField('تاریخ عضویت', default=timezone.now)
    last_login = models.DateTimeField('آخرین ورود', blank=True, null=True)
    
    # Email verification
    is_email_verified = models.BooleanField('ایمیل تایید شده', default=False)
    email_verification_token = models.CharField('توکن تایید ایمیل', max_length=100, blank=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type']
    
    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
    
    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)
    
    def save(self, *args, **kwargs):
        """Override save to enforce security rules"""
        # معلم‌ها و زبان‌آموزان نمی‌توانند superuser باشند
        # فقط از طریق console django می‌توان superuser ایجاد کرد
        if self.user_type in ['teacher', 'student']:
            self.is_superuser = False
            self.is_staff = False
        
        super().save(*args, **kwargs)
    
    def generate_email_verification_token(self):
        """Generate a verification token for email confirmation"""
        import secrets
        token = secrets.token_urlsafe(32)
        self.email_verification_token = token
        # Use update_fields to avoid recursion
        super(User, self).save(update_fields=['email_verification_token'])
        return token
    
    @property
    def is_student(self):
        """Check if user is a student"""
        return self.user_type == 'student'
    
    @property
    def is_teacher(self):
        """Check if user is a teacher"""
        return self.user_type == 'teacher'


class Student(models.Model):
    """Student profile extending the custom user"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    
    # Student specific fields
    national_id = models.CharField("کد ملی", max_length=10, blank=True, null=True)
    phone_number = models.CharField("شماره تلفن", max_length=20, blank=True)
    date_of_birth = models.DateField("تاریخ تولد", null=True, blank=True)
    address = models.TextField("آدرس", blank=True)
    
    # Academic info
    english_level = models.CharField("سطح زبان انگلیسی", max_length=20, blank=True)
    goals = models.TextField("اهداف یادگیری", blank=True)
    
    # Tracking fields
    enrollment_date = models.DateTimeField("تاریخ ثبت‌نام", default=timezone.now)
    last_activity = models.DateTimeField("آخرین فعالیت", auto_now=True)
    
    class Meta:
        verbose_name = "دانش‌آموز"
        verbose_name_plural = "دانش‌آموزان"
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.user.email}"
    
    @classmethod
    def create_for_user(cls, user, **profile_data):
        """Create a student profile for a user"""
        return cls.objects.create(
            user=user,
            phone_number=profile_data.get('phone_number', ''),
            date_of_birth=profile_data.get('date_of_birth'),
            english_level=profile_data.get('english_level', ''),
            goals=profile_data.get('goals', '')
        )
    
    def get_profile_completion_percentage(self):
        """Calculate the completion percentage of the student's profile"""
        total_fields = 8  # Total number of profile fields to check
        completed_fields = 0
        
        # Check User fields
        if self.user.first_name:
            completed_fields += 1
        if self.user.last_name:
            completed_fields += 1
        if self.user.email:  # This is always required
            completed_fields += 1
            
        # Check Student fields
        if self.national_id:
            completed_fields += 1
        if self.phone_number:
            completed_fields += 1
        if self.date_of_birth:
            completed_fields += 1
        if self.english_level:
            completed_fields += 1
        if self.goals:
            completed_fields += 1
            
        return int((completed_fields / total_fields) * 100)


class TeacherApplicationManager(models.Manager):
    """Custom manager for TeacherApplication"""
    
    def for_email(self, email):
        """Filter applications by email"""
        return self.filter(email__iexact=email)


class TeacherApplication(models.Model):
    """Model for teacher application submissions"""
    
    STATUS_CHOICES = (
        ('pending', 'در انتظار بررسی'),
        ('accepted', 'پذیرفته شده'),
        ('rejected', 'رد شده'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Personal Information
    first_name = models.CharField('نام', max_length=30)
    last_name = models.CharField('نام خانوادگی', max_length=30)
    email = models.EmailField('آدرس ایمیل', unique=True)
    phone_number = models.CharField('شماره تلفن', max_length=20)
    
    # Professional Information
    education = models.TextField('تحصیلات')
    experience = models.TextField('تجربه تدریس')
    certifications = models.TextField('گواهینامه‌ها', blank=True)
    specialties = models.TextField('تخصص‌ها')
    
    # Additional Information
    motivation = models.TextField('انگیزه همکاری')
    cv_file = models.FileField('فایل رزومه', upload_to='teacher_applications/', blank=True)
    
    # Application Status
    status = models.CharField('وضعیت', max_length=10, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField('یادداشت ادمین', blank=True)
    
    # Timestamps
    submitted_at = models.DateTimeField('تاریخ ارسال', default=timezone.now)
    reviewed_at = models.DateTimeField('تاریخ بررسی', blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    
    objects = TeacherApplicationManager()
    
    class Meta:
        verbose_name = "درخواست همکاری مدرس"
        verbose_name_plural = "درخواست‌های همکاری مدرس"
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_status_display()}"
    
    def mark_as_accepted(self, reviewed_by_user):
        """Mark application as accepted and allow teacher registration"""
        self.status = 'accepted'
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by_user
        self.save()
    
    def mark_as_rejected(self, reviewed_by_user, admin_notes=""):
        """Mark application as rejected"""
        self.status = 'rejected'
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewed_by_user
        self.admin_notes = admin_notes
        self.save()


class Teacher(models.Model):
    """Teacher profile extending the custom user"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    application = models.OneToOneField(TeacherApplication, on_delete=models.CASCADE, related_name='teacher_account')
    
    # Professional Information
    bio = models.TextField('بیوگرافی', blank=True)
    specialties = models.TextField('تخصص‌ها', default='')
    hourly_rate = models.DecimalField('نرخ ساعتی', max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Status
    is_active = models.BooleanField('فعال', default=True)
    is_verified = models.BooleanField('تایید شده', default=False)
    
    # Tracking
    joined_at = models.DateTimeField('تاریخ پیوستن', default=timezone.now)
    last_activity = models.DateTimeField('آخرین فعالیت', auto_now=True)

    telegram_username = models.CharField('نام کاربری تلگرام', max_length=100, blank=True)
    whatsapp_number = models.CharField('شماره واتساپ', max_length=20, blank=True)
    instagram_username = models.CharField('نام کاربری اینستاگرام', max_length=100, blank=True)
    linkedin_username = models.CharField('نام کاربری لینکدین', max_length=100, blank=True)
    youtube_username = models.CharField('نام کاربری یوتیوب', max_length=100, blank=True)
    
    # Education
    education_level = models.CharField('سطح تحصیلات', max_length=100, blank=True)
    education_field = models.CharField('رشته تحصیلات', max_length=100, blank=True)
    education_institution = models.CharField('موسسه تحصیلات', max_length=100, blank=True)
    education_degree = models.CharField('مدرک تحصیلات', max_length=100, blank=True)
    education_start_date = models.DateField('تاریخ شروع تحصیلات', blank=True, null=True)
    education_end_date = models.DateField('تاریخ پایان تحصیلات', blank=True, null=True)
    
    # Experience
    experience_years = models.IntegerField('سال تجربه', blank=True, null=True)
    experience_description = models.TextField('توضیحات تجربه', blank=True)

    # Availability
    availability_days = models.TextField('روزهای فعالیت', blank=True)
    availability_hours = models.TextField('ساعات فعالیت', blank=True)
    availability_description = models.TextField('توضیحات فعالیت', blank=True)

    
    class Meta:
        verbose_name = "مدرس"
        verbose_name_plural = "مدرسان"
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.user.email}"
    
    def get_profile_completion_percentage(self):
        """Calculate profile completion percentage"""
        total_fields = 8
        completed_fields = 0
        
        # Check user fields
        if self.user.first_name and self.user.last_name:
            completed_fields += 1
        if self.user.email:
            completed_fields += 1
            
        # Check teacher fields
        if self.bio:
            completed_fields += 1
        if self.specialties:
            completed_fields += 1
        if self.hourly_rate:
            completed_fields += 1
        if hasattr(self, 'image') and self.image:
            completed_fields += 1
        if self.is_verified:
            completed_fields += 1
        if self.application and self.application.education:
            completed_fields += 1
            
        return int((completed_fields / total_fields) * 100)
    
    def get_profile_completion_offset(self):
        """Get SVG circle stroke-dashoffset for profile completion ring"""
        percentage = self.get_profile_completion_percentage()
        circumference = 2 * 3.14159 * 52  # radius = 52
        return circumference - (percentage / 100) * circumference
    
    @property
    def rating(self):
        """Calculate teacher rating based on course reviews (placeholder)"""
        # This is a placeholder - implement actual rating calculation
        # based on course reviews when review system is implemented
        return None
    
    @property
    def registration_status(self):
        """Get registration status"""
        if self.is_verified and self.is_active:
            return 'approved'
        elif self.is_active:
            return 'pending'
        else:
            return 'inactive'


