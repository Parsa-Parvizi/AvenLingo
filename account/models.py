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

class AuthSystemSettings(models.Model):
    """Global settings for the authentication system"""
    
    # Site Information
    site_name = models.CharField('نام سایت', max_length=100, default='آکادمی زبان مبینا')
    site_logo = models.ImageField('لوگو سایت', upload_to='site/', blank=True, null=True)
    
    # Registration Settings
    student_registration_enabled = models.BooleanField('ثبت‌نام دانش‌آموز فعال', default=True)
    teacher_application_enabled = models.BooleanField('درخواست همکاری مدرس فعال', default=True)
    email_verification_required = models.BooleanField('تایید ایمیل اجباری', default=True)
    
    # Default Messages
    welcome_message = models.TextField('پیام خوش‌آمدگویی', default='به آکادمی زبان مبینا خوش آمدید!')
    maintenance_message = models.TextField('پیام تعمیرات', default='سایت در حال به‌روزرسانی است. لطفاً بعداً مراجعه کنید.')
    
    # Contact Information
    support_email = models.EmailField('ایمیل پشتیبانی', default='support@academy.com')
    admin_phone = models.CharField('تلفن ادمین', max_length=20, default='09123456789')
    
    # Social Media
    instagram_url = models.URLField('اینستاگرام', blank=True)
    telegram_url = models.URLField('تلگرام', blank=True)
    whatsapp_number = models.CharField('واتساپ', max_length=20, blank=True, default='09123456789')
    
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('تاریخ به‌روزرسانی', auto_now=True)
    
    class Meta:
        verbose_name = 'تنظیمات سیستم احراز هویت'
        verbose_name_plural = 'تنظیمات سیستم احراز هویت'
    
    def __str__(self):
        return f'تنظیمات {self.site_name}'
    
    def get_instagram_url(self):
        """Get Instagram URL with fallback to settings default"""
        from django.conf import settings
        if self.instagram_url:
            return self.instagram_url
        return getattr(settings, 'EXTERNAL_URLS', {}).get('INSTAGRAM_DEFAULT', '')
    
    def get_telegram_url(self):
        """Get Telegram URL with fallback to settings default"""
        from django.conf import settings
        if self.telegram_url:
            return self.telegram_url
        return getattr(settings, 'EXTERNAL_URLS', {}).get('TELEGRAM_DEFAULT', '')
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and AuthSystemSettings.objects.exists():
            raise ValueError('فقط یک تنظیمات اصلی مجاز است')
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create the settings instance"""
        settings, created = cls.objects.get_or_create(
            id=1,
            defaults={
                'site_name': 'آکادمی زبان مبینا',
                'welcome_message': 'به آکادمی زبان مبینا خوش آمدید!',
                'support_email': 'support@academy.com',
            }
        )
        return settings


class FormConfiguration(models.Model):
    """Configuration for form labels, placeholders, and help texts"""
    
    FORM_TYPE_CHOICES = (
        ('student_registration', 'ثبت‌نام دانش‌آموز'),
        ('teacher_application', 'درخواست همکاری مدرس'),
        ('login', 'ورود'),
        ('profile_update', 'به‌روزرسانی پروفایل'),
    )
    
    form_type = models.CharField('نوع فرم', max_length=30, choices=FORM_TYPE_CHOICES, unique=True)
    
    # Form Titles and Descriptions
    title = models.CharField('عنوان فرم', max_length=100)
    description = models.TextField('توضیحات فرم', blank=True)
    success_message = models.TextField('پیام موفقیت')
    
    # Field Labels (JSON format for flexibility)
    field_labels = models.JSONField('برچسب‌های فیلدها', default=dict, blank=True)
    field_placeholders = models.JSONField('متن‌های placeholder', default=dict, blank=True)
    field_help_texts = models.JSONField('متن‌های راهنما', default=dict, blank=True)
    
    # Validation Messages
    validation_messages = models.JSONField('پیام‌های اعتبارسنجی', default=dict, blank=True)
    
    # Form Styling
    submit_button_text = models.CharField('متن دکمه ارسال', max_length=50, default='ارسال')
    submit_button_color = models.CharField('رنگ دکمه ارسال', max_length=20, default='primary')
    
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('تاریخ به‌روزرسانی', auto_now=True)
    
    class Meta:
        verbose_name = 'پیکربندی فرم'
        verbose_name_plural = 'پیکربندی فرم‌ها'
    
    def __str__(self):
        return f'{self.get_form_type_display()} - {self.title}'
    
    @classmethod
    def get_form_config(cls, form_type):
        """Get configuration for a specific form type"""
        try:
            return cls.objects.get(form_type=form_type, is_active=True)
        except cls.DoesNotExist:
            # Return default configuration
            defaults = cls._get_default_config(form_type)
            return cls.objects.create(form_type=form_type, **defaults)
    
    @classmethod
    def _get_default_config(cls, form_type):
        """Default configurations for different form types"""
        defaults = {
            'student_registration': {
                'title': 'ثبت‌نام دانش‌آموز',
                'description': 'برای شروع یادگیری، لطفاً فرم زیر را تکمیل کنید.',
                'success_message': 'ثبت‌نام شما با موفقیت انجام شد! لطفاً ایمیل خود را بررسی کنید.',
                'field_labels': {
                    'first_name': 'نام',
                    'last_name': 'نام خانوادگی',
                    'email': 'آدرس ایمیل',
                    'password1': 'رمز عبور',
                    'password2': 'تکرار رمز عبور',
                    'phone_number': 'شماره تلفن',
                    'english_level': 'سطح زبان انگلیسی',
                },
                'field_placeholders': {
                    'first_name': 'نام خود را وارد کنید',
                    'last_name': 'نام خانوادگی خود را وارد کنید',
                    'email': 'example@email.com',
                    'password1': 'رمز عبور قوی انتخاب کنید',
                    'password2': 'رمز عبور را دوباره وارد کنید',
                    'phone_number': '09123456789',
                },
                'submit_button_text': 'ثبت‌نام',
            },
            'teacher_application': {
                'title': 'درخواست همکاری مدرس',
                'description': 'برای همکاری با آکادمی ما، لطفاً فرم زیر را با دقت تکمیل کنید.',
                'success_message': 'درخواست شما با موفقیت ارسال شد. پس از بررسی، نتیجه به ایمیل شما اطلاع داده خواهد شد.',
                'field_labels': {
                    'first_name': 'نام',
                    'last_name': 'نام خانوادگی',
                    'email': 'آدرس ایمیل',
                    'phone_number': 'شماره تلفن',
                    'education': 'تحصیلات',
                    'experience': 'تجربه تدریس',
                    'certifications': 'گواهینامه‌ها',
                    'specialties': 'تخصص‌ها',
                    'motivation': 'انگیزه همکاری',
                    'cv_file': 'فایل رزومه',
                },
                'submit_button_text': 'ارسال درخواست',
            },
            'login': {
                'title': 'ورود به حساب کاربری',
                'description': 'برای دسترسی به پنل کاربری خود وارد شوید.',
                'success_message': 'خوش آمدید! شما با موفقیت وارد شدید.',
                'field_labels': {
                    'email': 'آدرس ایمیل',
                    'password': 'رمز عبور',
                },
                'field_placeholders': {
                    'email': 'ایمیل خود را وارد کنید',
                    'password': 'رمز عبور خود را وارد کنید',
                },
                'submit_button_text': 'ورود',
            },
        }
        return defaults.get(form_type, {
            'title': form_type.replace('_', ' ').title(),
            'description': '',
            'success_message': 'عملیات با موفقیت انجام شد.',
            'submit_button_text': 'ارسال',
        })


class EmailTemplate(models.Model):
    """Email templates for different scenarios"""
    
    TEMPLATE_TYPE_CHOICES = (
        ('email_verification', 'تایید ایمیل'),
        ('application_received', 'دریافت درخواست'),
        ('application_accepted', 'پذیرش درخواست'),
        ('application_rejected', 'رد درخواست'),
        ('welcome_student', 'خوش‌آمدگویی دانش‌آموز'),
        ('welcome_teacher', 'خوش‌آمدگویی مدرس'),
        ('password_reset', 'بازیابی رمز عبور'),
    )
    
    template_type = models.CharField('نوع قالب', max_length=30, choices=TEMPLATE_TYPE_CHOICES, unique=True)
    
    subject = models.CharField('موضوع ایمیل', max_length=200)
    html_content = models.TextField('محتوای HTML')
    text_content = models.TextField('محتوای متنی', blank=True)
    
    # Template variables help text
    available_variables = models.TextField('متغیرهای قابل استفاده', 
        help_text='متغیرهایی که در این قالب قابل استفاده هستند (مثل {{first_name}}, {{site_name}})')
    
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('تاریخ به‌روزرسانی', auto_now=True)
    
    class Meta:
        verbose_name = 'قالب ایمیل'
        verbose_name_plural = 'قالب‌های ایمیل'
    
    def __str__(self):
        return f'{self.get_template_type_display()} - {self.subject}'
    
    @classmethod
    def get_template(cls, template_type):
        """Get email template by type"""
        try:
            return cls.objects.get(template_type=template_type, is_active=True)
        except cls.DoesNotExist:
            # Create default template
            defaults = cls._get_default_template(template_type)
            return cls.objects.create(template_type=template_type, **defaults)
    
    @classmethod
    def _get_default_template(cls, template_type):
        """Default email templates"""
        defaults = {
            'email_verification': {
                'subject': 'تایید آدرس ایمیل شما',
                'html_content': '''
                    <h2>سلام {{first_name}}!</h2>
                    <p>برای تکمیل ثبت‌نام در {{site_name}}، لطفاً روی لینک زیر کلیک کنید:</p>
                    <a href="{{verification_link}}" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">تایید ایمیل</a>
                    <p>این لینک تا ۲۴ ساعت اعتبار دارد.</p>
                ''',
                'text_content': 'سلام {{first_name}}! برای تایید ایمیل خود، لطفاً به آدرس زیر مراجعه کنید: {{verification_link}}',
                'available_variables': '{{first_name}}, {{last_name}}, {{site_name}}, {{verification_link}}',
            },
            'application_received': {
                'subject': 'دریافت درخواست همکاری شما',
                'html_content': '''
                    <h2>سلام {{first_name}} {{last_name}}!</h2>
                    <p>درخواست همکاری شما در {{site_name}} با موفقیت دریافت شد.</p>
                    <p>تیم ما درخواست شما را بررسی خواهد کرد و در کوتاه‌ترین زمان ممکن نتیجه را به اطلاع شما خواهد رساند.</p>
                    <p>با تشکر از شما</p>
                ''',
                'available_variables': '{{first_name}}, {{last_name}}, {{site_name}}',
            },
            'application_accepted': {
                'subject': 'تبریک! درخواست همکاری شما پذیرفته شد',
                'html_content': '''
                    <h2>تبریک {{first_name}}!</h2>
                    <p>خوشحالیم که اعلام کنیم درخواست همکاری شما در {{site_name}} پذیرفته شده است.</p>
                    <p>اکنون می‌توانید با ایمیل {{email}} ثبت‌نام کنید:</p>
                    <a href="{{registration_link}}">ثبت‌نام مدرس</a>
                    <p>به تیم ما خوش آمدید!</p>
                ''',
                'available_variables': '{{first_name}}, {{last_name}}, {{email}}, {{site_name}}, {{registration_link}}',
            },
        }
        return defaults.get(template_type, {
            'subject': f'پیام از {template_type}',
            'html_content': '<p>{{message}}</p>',
            'available_variables': '{{first_name}}, {{last_name}}, {{site_name}}',
        })


class PageContent(models.Model):
    """Editable content for different pages"""
    
    PAGE_TYPE_CHOICES = (
        ('student_dashboard', 'داشبورد دانش‌آموز'),
        ('teacher_dashboard', 'داشبورد مدرس'),
        ('teacher_apply', 'درخواست همکاری'),
        ('login_page', 'صفحه ورود'),
        ('registration_page', 'صفحه ثبت‌نام'),
        ('email_verification', 'تایید ایمیل'),
        ('footer', 'فوتر'),
    )
    
    page_type = models.CharField('نوع صفحه', max_length=30, choices=PAGE_TYPE_CHOICES, unique=True)
    
    # Content sections
    hero_title = models.CharField('عنوان اصلی', max_length=200, blank=True)
    hero_subtitle = models.TextField('زیرعنوان', blank=True)
    
    content_sections = models.JSONField('بخش‌های محتوا', default=list, blank=True,
        help_text='لیستی از بخش‌های محتوا با title و content')
    
    # Call-to-action buttons
    primary_cta_text = models.CharField('متن دکمه اصلی', max_length=50, blank=True)
    primary_cta_url = models.CharField('لینک دکمه اصلی', max_length=200, blank=True)
    
    secondary_cta_text = models.CharField('متن دکمه ثانویه', max_length=50, blank=True)
    secondary_cta_url = models.CharField('لینک دکمه ثانویه', max_length=200, blank=True)
    
    # Images
    hero_image = models.ImageField('تصویر اصلی', upload_to='page_content/', blank=True, null=True)
    background_image = models.ImageField('تصویر پس‌زمینه', upload_to='page_content/', blank=True, null=True)
    
    is_active = models.BooleanField('فعال', default=True)
    created_at = models.DateTimeField('تاریخ ایجاد', auto_now_add=True)
    updated_at = models.DateTimeField('تاریخ به‌روزرسانی', auto_now=True)
    
    class Meta:
        verbose_name = 'محتوای صفحه'
        verbose_name_plural = 'محتوای صفحات'
    
    def __str__(self):
        return f'{self.get_page_type_display()} - {self.hero_title}'
    
    @classmethod
    def get_page_content(cls, page_type):
        """Get content for a specific page"""
        try:
            return cls.objects.get(page_type=page_type, is_active=True)
        except cls.DoesNotExist:
            # Create default content
            defaults = cls._get_default_content(page_type)
            return cls.objects.create(page_type=page_type, **defaults)
    
    @classmethod
    def _get_default_content(cls, page_type):
        """Default content for different pages"""
        defaults = {
            'student_dashboard': {
                'hero_title': 'خوش آمدید!',
                'hero_subtitle': 'به داشبورد دانش‌آموزی خود خوش آمدید.',
                'content_sections': [
                    {'title': 'دوره‌های من', 'content': 'مشاهده دوره‌هایی که در آن‌ها ثبت‌نام کرده‌اید.'},
                    {'title': 'پیشرفت تحصیلی', 'content': 'مشاهده گزارش پیشرفت و نمرات خود.'},
                ],
                'primary_cta_text': 'مشاهده دوره‌ها',
                'primary_cta_url': '/courses/',
            },
            'teacher_dashboard': {
                'hero_title': 'پنل مدرس',
                'hero_subtitle': 'مدیریت کلاس‌ها و دانش‌آموزان خود.',
                'content_sections': [
                    {'title': 'کلاس‌های من', 'content': 'مشاهده و مدیریت کلاس‌های در حال برگزاری.'},
                    {'title': 'دانش‌آموزان', 'content': 'مشاهده لیست دانش‌آموزان و عملکرد آن‌ها.'},
                ],
                'primary_cta_text': 'مدیریت کلاس‌ها',
                'primary_cta_url': '/teacher/classes/',
            },
            'teacher_apply': {
                'hero_title': 'همکاری با ما',
                'hero_subtitle': 'به تیم مدرسان حرفه‌ای ما بپیوندید.',
                'content_sections': [
                    {'title': 'چرا با ما؟', 'content': 'محیط کاری حرفه‌ای، دستمزد رقابتی، فرصت رشد.'},
                    {'title': 'شرایط همکاری', 'content': 'مدرک مرتبط، تجربه تدریس، تسلط به زبان انگلیسی.'},
                ],
            },
        }
        return defaults.get(page_type, {
            'hero_title': page_type.replace('_', ' ').title(),
            'hero_subtitle': '',
            'content_sections': [],
        })


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
    
    class Meta:
        verbose_name = "مدرس"
        verbose_name_plural = "مدرسان"
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.user.email}"


