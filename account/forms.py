from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import datetime, timedelta
import re
import logging
import secrets
import hashlib

from .models import Student, Teacher, TeacherApplication

User = get_user_model()
logger = logging.getLogger('account.forms')


class EnhancedValidationMixin:
    """Mixin for enhanced form validation and security"""
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Add common CSS classes and attributes
        for field_name, field in self.fields.items():
            if not hasattr(field.widget.attrs, 'class'):
                field.widget.attrs['class'] = 'form-control'
            
            # Add real-time validation attributes
            if field_name in ['email', 'username']:
                field.widget.attrs.update({
                    'data-validation': 'email' if field_name == 'email' else 'username',
                    'data-validation-url': '/auth/validate-field/',
                })
            
            elif field_name in ['password1', 'password']:
                field.widget.attrs.update({
                    'data-validation': 'password',
                    'data-strength-meter': 'true',
                    'autocomplete': 'new-password' if field_name == 'password1' else 'current-password'
                })
            
            elif field_name == 'phone_number':
                field.widget.attrs.update({
                    'data-validation': 'phone',
                    'pattern': r'09\d{9}',
                    'title': 'شماره موبایل باید به فرمت 09123456789 باشد'
                })
    
    def check_rate_limit(self, identifier, action_type='form_submit', limit=5, window_minutes=15):
        """Enhanced rate limiting with different action types"""
        if not self.request:
            return False
            
        cache_key = f"rate_limit_{action_type}_{identifier}"
        # In a real implementation, you would use database
        # For now, we'll use session-based simple tracking
        
        current_time = timezone.now()
        session_key = f"{cache_key}_attempts"
        
        if session_key not in self.request.session:
            self.request.session[session_key] = []
        
        attempts = self.request.session[session_key]
        # Remove old attempts outside the window
        attempts = [attempt for attempt in attempts 
                   if (current_time - datetime.fromisoformat(attempt)).total_seconds() < window_minutes * 60]
        
        if len(attempts) >= limit:
            logger.warning(f"Rate limit exceeded for {identifier} in {action_type}")
            return True
        
        attempts.append(current_time.isoformat())
        self.request.session[session_key] = attempts
        return False
    
    def validate_suspicious_patterns(self, text, field_name):
        """Enhanced suspicious content detection"""
        if not text:
            return text
            
        suspicious_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onclick\s*=',
            r'onerror\s*=',
            r'onload\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'eval\s*\(',
            r'expression\s*\(',
            r'url\s*\(',
            r'@import',
            r'\\x[0-9a-f]{2}',  # Hex encoding
            r'&#x[0-9a-f]+;',   # HTML hex entities
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Suspicious content detected in {field_name}: {pattern}")
                raise ValidationError(f'محتوای وارد شده در فیلد {field_name} مجاز نیست.')
        
        return text
    
    def clean_text_field(self, field_name, max_length=None, min_length=None, required=True):
        """Enhanced text field cleaning with comprehensive validation"""
        value = self.cleaned_data.get(field_name, '').strip()
        
        if required and not value:
            raise ValidationError(f'فیلد {field_name} الزامی است.')
        
        if not value:
            return value
        
        # Length validation
        if min_length and len(value) < min_length:
            raise ValidationError(f'حداقل طول مجاز برای {field_name}: {min_length} کاراکتر')
        
        if max_length and len(value) > max_length:
            raise ValidationError(f'حداکثر طول مجاز برای {field_name}: {max_length} کاراکتر')
        
        # Suspicious content validation
        value = self.validate_suspicious_patterns(value, field_name)
        
        return value


class StudentRegistrationForm(EnhancedValidationMixin, UserCreationForm):
    """Enhanced registration form for students with improved validation and UX"""
    
    first_name = forms.CharField(
        max_length=30,
        label='نام',
        help_text='نام حقیقی خود را وارد کنید',
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'نام خود را وارد کنید',
            'autocomplete': 'given-name',
            'data-validation': 'name',
            'pattern': r'^[\u0600-\u06FFa-zA-Z\s]+$',
            'title': 'فقط حروف فارسی و انگلیسی مجاز است'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        label='نام خانوادگی',
        help_text='نام خانوادگی حقیقی خود را وارد کنید',
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'نام خانوادگی خود را وارد کنید',
            'autocomplete': 'family-name',
            'data-validation': 'name',
            'pattern': r'^[\u0600-\u06FFa-zA-Z\s]+$',
            'title': 'فقط حروف فارسی و انگلیسی مجاز است'
        })
    )
    
    email = forms.EmailField(
        label='آدرس ایمیل',
        help_text='ایمیل معتبر خود را وارد کنید. کد تأیید به این آدرس ارسال خواهد شد.',
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'example@email.com',
            'autocomplete': 'email',
            'data-validation': 'email',
            'data-validation-url': '/auth/validate-email/',
            'data-realtime': 'true'
        })
    )
    
    phone_number = forms.CharField(
        max_length=20,
        label='شماره موبایل',
        required=False,
        help_text='شماره موبایل خود را به فرمت 09123456789 وارد کنید',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '09123456789',
            'autocomplete': 'tel',
            'data-validation': 'phone',
            'pattern': r'09\d{9}',
            'title': 'شماره موبایل باید به فرمت 09123456789 باشد',
            'data-mask': '09999999999'
        })
    )
    
    date_of_birth = forms.DateField(
        required=False,
        label='تاریخ تولد',
        help_text='تاریخ تولد برای تعیین گروه سنی مناسب',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'autocomplete': 'bday',
            'max': datetime.now().date().isoformat(),  # Can't be future date
            'min': (datetime.now().date() - timedelta(days=36500)).isoformat()  # Max 100 years old
        })
    )
    
    # Enhanced honeypot field
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'style': 'position: absolute; left: -9999px; opacity: 0;',
            'tabindex': '-1',
            'autocomplete': 'off',
            'aria-hidden': 'true'
        })
    )
    
    # Progressive disclosure fields
    english_level = forms.ChoiceField(
        choices=[
            ('', 'انتخاب کنید...'),
            ('beginner', 'مبتدی'),
            ('elementary', 'ابتدایی'),
            ('pre_intermediate', 'پیش متوسط'),
            ('intermediate', 'متوسط'),
            ('upper_intermediate', 'فوق متوسط'),
            ('advanced', 'پیشرفته'),
        ],
        required=False,
        label='سطح زبان انگلیسی',
        help_text='سطح فعلی زبان انگلیسی خود را انتخاب کنید',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-step': '2'
        })
    )
    
    learning_goals = forms.MultipleChoiceField(
        choices=[
            ('conversation', 'تقویت مکالمه'),
            ('grammar', 'یادگیری گرامر'),
            ('business', 'انگلیسی تجاری'),
            ('academic', 'آمادگی آزمون'),
            ('travel', 'انگلیسی سفر'),
            ('job', 'ارتقای شغلی'),
        ],
        required=False,
        label='اهداف یادگیری',
        help_text='اهداف خود از یادگیری زبان انگلیسی را انتخاب کنید',
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input',
            'data-step': '2'
        })
    )
    
    # Terms and conditions with enhanced validation
    terms_accepted = forms.BooleanField(
        required=True,
        label='',
        help_text='',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'data-required': 'true',
            'data-validation': 'terms'
        })
    )
    
    # Privacy policy acceptance
    privacy_accepted = forms.BooleanField(
        required=True,
        label='',
        help_text='',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'data-required': 'true',
            'data-validation': 'privacy'
        })
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Enhanced password fields with better UX
        self.fields['password1'].help_text = (
            "رمز عبور باید حداقل ۸ کاراکتر باشد"
        )
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'رمز عبور خود را وارد کنید',
            'autocomplete': 'new-password',
            'data-validation': 'password',
            'data-strength-meter': 'true',
            'data-realtime': 'true'
        })
        
        self.fields['password2'].help_text = "رمز عبور خود را مجدداً وارد کنید"
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'تکرار رمز عبور',
            'autocomplete': 'new-password',
            'data-validation': 'password-confirm',
            'data-match': 'password1'
        })

    def clean_website(self):
        """Honeypot validation"""
        website = self.cleaned_data.get('website')
        if website:
            logger.warning(f"Bot detected - honeypot filled: {website}")
            raise ValidationError('Bot detected')
        return website

    def clean_first_name(self):
        return self.clean_text_field('first_name', max_length=30, min_length=2)

    def clean_last_name(self):
        return self.clean_text_field('last_name', max_length=30, min_length=2)

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        
        if not email:
            raise ValidationError('آدرس ایمیل الزامی است.')
        
        # Enhanced email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValidationError('فرمت آدرس ایمیل صحیح نیست.')
        
        # Block temporary email domains
        blocked_domains = [
            '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
            'tempmail.org', 'throwaway.email', 'temp-mail.org'
        ]
        domain = email.split('@')[1].lower()
        if domain in blocked_domains:
            raise ValidationError('استفاده از آدرس ایمیل موقت مجاز نیست.')
        
        # Check for existing email
        if User.objects.filter(email=email).exists():
            raise ValidationError('کاربری با این آدرس ایمیل قبلاً ثبت‌نام کرده است.')
        
        # Rate limiting for email validation
        if self.check_rate_limit(email, 'email_check', limit=3, window_minutes=5):
            raise ValidationError('تعداد درخواست‌های شما زیاد است. لطفاً کمی صبر کنید.')
        
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        
        if phone:
            # Remove any non-digit characters
            phone_digits = re.sub(r'\D', '', phone)
            
            if not re.match(r'^09\d{9}$', phone_digits):
                raise ValidationError('شماره موبایل باید به فرمت 09123456789 باشد.')
            
            # Check for existing phone number
            if Student.objects.filter(phone_number=phone_digits).exists():
                raise ValidationError('کاربری با این شماره موبایل قبلاً ثبت‌نام کرده است.')
            
            return phone_digits
        
        return phone

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        
        if dob:
            today = datetime.now().date()
            age = (today - dob).days // 365
            
            if age < 6:
                raise ValidationError('حداقل سن مجاز ۶ سال است.')
            
            if age > 100:
                raise ValidationError('حداکثر سن مجاز ۱۰۰ سال است.')
        
        return dob

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        
        if password:
            if len(password) < 8:
                raise ValidationError('رمز عبور باید حداقل ۸ کاراکتر باشد.')
        
        return password

    def clean(self):
        cleaned_data = super().clean()
        
        # Cross-field validation
        first_name = cleaned_data.get('first_name', '')
        last_name = cleaned_data.get('last_name', '')
        email = cleaned_data.get('email', '')
        
        # Check if name appears in email (may indicate fake account)
        if first_name and last_name and email:
            full_name_parts = [first_name.lower(), last_name.lower()]
            email_username = email.split('@')[0].lower()
            
            # If email username contains both first and last name, it might be suspicious
            if all(part in email_username for part in full_name_parts):
                logger.info(f"Name matches email pattern for {email}")
        
        # Rate limiting for form submission
        user_identifier = self.request.META.get('REMOTE_ADDR', 'unknown') if self.request else 'unknown'
        if self.check_rate_limit(user_identifier, 'registration', limit=3, window_minutes=30):
            raise ValidationError('تعداد تلاش‌های ثبت‌نام شما زیاد است. لطفاً ۳۰ دقیقه صبر کنید.')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.user_type = 'student'
        user.is_active = True  # Will be set to False if email verification is required
        
        if commit:
            user.save()
            
            # Create student profile
            student = Student.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number', ''),
                date_of_birth=self.cleaned_data.get('date_of_birth'),
                english_level=self.cleaned_data.get('english_level', ''),
                goals=', '.join(self.cleaned_data.get('learning_goals', []))
            )
            
            logger.info(f"New student registered: {user.email}")
        
        return user


class TeacherRegistrationForm(UserCreationForm):
    """Registration form for teachers (only allowed after application acceptance)"""
    
    first_name = forms.CharField(
        max_length=30,
        label='نام',
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True})
    )
    last_name = forms.CharField(
        max_length=30,
        label='نام خانوادگی',
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True})
    )
    email = forms.EmailField(
        label='آدرس ایمیل',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'readonly': True})
    )
    
    password1 = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور خود را وارد کنید'})
    )
    password2 = forms.CharField(
        label='تایید رمز عبور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور خود را مجدد وارد کنید'})
    )
    
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'درباره خود بنویسید...'}),
        label='بیوگرافی',
        required=False
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application', None)
        super().__init__(*args, **kwargs)
        
        if self.application:
            self.fields['first_name'].initial = self.application.first_name
            self.fields['last_name'].initial = self.application.last_name
            self.fields['email'].initial = self.application.email
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if not self.application or self.application.email != email:
            raise ValidationError('شما تنها می‌توانید با ایمیل تایید شده ثبت‌نام کنید.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'teacher'
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create teacher profile
            Teacher.objects.create(
                user=user,
                application=self.application,
                bio=self.cleaned_data.get('bio', ''),
                specialties=self.application.specialties
            )
        return user


class CustomLoginForm(EnhancedValidationMixin, AuthenticationForm):
    """Enhanced login form with security features and better UX"""
    
    username = forms.CharField(
        label='ایمیل یا شماره موبایل',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ایمیل یا شماره موبایل (0912...)',
            'autocomplete': 'username',
            'required': True,
            'inputmode': 'email',
            'data-validation': 'identifier',
            'data-realtime': 'true'
        })
    )
    
    password = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور خود را وارد کنید',
            'autocomplete': 'current-password',
            'required': True,
            'data-validation': 'password'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        label='مرا به خاطر بسپار',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'data-session-extend': 'true'
        })
    )
    
    # Enhanced honeypot
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'style': 'position: absolute; left: -9999px; opacity: 0;',
            'tabindex': '-1',
            'autocomplete': 'off',
            'aria-hidden': 'true'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_website(self):
        """Enhanced honeypot validation"""
        website = self.cleaned_data.get('website')
        if website:
            logger.warning(f"Bot detected in login - honeypot filled: {website}")
            # Don't immediately raise error, log and track instead
            if self.request:
                self.request.session['bot_detected'] = True
        return website

    def clean_username(self):
        username = self.cleaned_data.get('username', '').lower().strip()
        
        if not username:
            raise ValidationError('ایمیل یا شماره موبایل الزامی است.')
        
        # Rate limiting for login attempts
        if self.check_rate_limit(username, 'login_attempt', limit=5, window_minutes=15):
            logger.warning(f"Login rate limit exceeded for {username}")
            raise ValidationError('تعداد تلاش‌های ورود شما زیاد است. لطفاً ۱۵ دقیقه صبر کنید.')
        
        return username

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            # Normalize identifier: if it looks like a phone, resolve to user's email
            identifier = username.strip().lower()
            phone_digits = re.sub(r'\D', '', identifier)
            if re.match(r'^09\d{9}$', phone_digits):
                try:
                    student = Student.objects.get(phone_number=phone_digits)
                    identifier = student.user.email.lower()
                except Student.DoesNotExist:
                    # No student with this phone
                    pass
            
            # Check for suspicious activity patterns
            if self.is_suspicious_activity():
                logger.warning(f"Suspicious login activity detected for {identifier}")
                raise ValidationError('فعالیت مشکوک شناسایی شد. لطفاً بعداً تلاش کنید.')
            
            # Standard authentication (Django expects username=email here)
            self.user_cache = authenticate(
                self.request, 
                username=identifier, 
                password=password
            )
            
            if self.user_cache is None:
                self.log_failed_attempt(identifier)
                raise ValidationError('شناسه (ایمیل/موبایل) یا رمز عبور اشتباه است.')
            else:
                self.confirm_login_allowed(self.user_cache)
                self.clear_failed_attempts(identifier)

        return self.cleaned_data

    def is_suspicious_activity(self):
        """Enhanced suspicious activity detection"""
        if not self.request:
            return False
        
        user_agent = self.request.META.get('HTTP_USER_AGENT', '').lower()
        
        # Check for suspicious user agents
        suspicious_agents = [
            'bot', 'crawler', 'spider', 'scraper', 'automated',
            'python-requests', 'curl', 'wget', 'libwww'
        ]
        
        for agent in suspicious_agents:
            if agent in user_agent:
                return True
        
        # Check for SQL injection patterns in any form data
        all_data = ' '.join(str(v) for v in self.data.values())
        sql_patterns = [
            r'union\s+select', r'drop\s+table', r'insert\s+into',
            r'delete\s+from', r'update\s+.*set', r'exec\s*\(',
            r'script\s*>', r'javascript:', r'vbscript:'
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, all_data, re.IGNORECASE):
                return True
        
        return False

    def log_failed_attempt(self, username):
        """Log failed login attempts"""
        if self.request:
            session_key = f"failed_attempts_{username}"
            if session_key not in self.request.session:
                self.request.session[session_key] = []
            
            self.request.session[session_key].append({
                'timestamp': timezone.now().isoformat(),
                'ip': self.request.META.get('REMOTE_ADDR', 'unknown'),
                'user_agent': self.request.META.get('HTTP_USER_AGENT', 'unknown')
            })
            
            logger.warning(f"Failed login attempt for {username} from IP {self.request.META.get('REMOTE_ADDR')}")

    def clear_failed_attempts(self, username):
        """Clear failed attempts after successful login"""
        if self.request:
            session_key = f"failed_attempts_{username}"
            if session_key in self.request.session:
                del self.request.session[session_key]


class TeacherApplicationForm(forms.ModelForm):
    """Form for teacher application submission"""
    
    class Meta:
        model = TeacherApplication
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'education', 'experience', 'certifications', 'specialties',
            'motivation', 'cv_file'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09123456789'}),
            'education': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'مدارک تحصیلی و رشته تحصیلی خود را شرح دهید...'}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'سوابق تدریس و تجربیات کاری خود را توضیح دهید...'}),
            'certifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'گواهینامه‌ها و مدارک مرتبط (اختیاری)'}),
            'specialties': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'تخصص‌های شما در تدریس زبان انگلیسی'}),
            'motivation': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'چرا می‌خواهید با ما همکاری کنید؟'}),
            'cv_file': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'email': 'آدرس ایمیل',
            'phone_number': 'شماره تلفن',
            'education': 'تحصیلات',
            'experience': 'تجربه تدریس',
            'certifications': 'گواهینامه‌ها',
            'specialties': 'تخصص‌ها',
            'motivation': 'انگیزه همکاری',
            'cv_file': 'فایل رزومه (اختیاری)',
        }
    
    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        # Basic Iranian phone number validation
        if phone and not re.match(r'^09\d{9}$', phone):
            raise ValidationError('شماره تلفن باید با 09 شروع شده و 11 رقم باشد.')
        return phone
    
    def clean_email(self):
        email = self.cleaned_data['email']
        # Check if email already has a pending or accepted application
        if TeacherApplication.objects.filter(email=email, status__in=['pending', 'accepted']).exists():
            raise ValidationError('با این ایمیل قبلاً درخواست ارسال شده است.')
        return email


class StudentProfileForm(forms.ModelForm):
    """Form for updating student profile"""
    
    class Meta:
        model = Student
        fields = ['phone_number', 'date_of_birth', 'address', 'english_level', 'goals']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'english_level': forms.Select(attrs={'class': 'form-control'}),
            'goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'phone_number': 'شماره تلفن',
            'date_of_birth': 'تاریخ تولد',
            'address': 'آدرس',
            'english_level': 'سطح زبان انگلیسی',
            'goals': 'اهداف یادگیری',
        }


class TeacherProfileForm(forms.ModelForm):
    """Form for updating teacher profile"""
    
    class Meta:
        model = Teacher
        fields = ['bio', 'specialties', 'hourly_rate']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'specialties': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'bio': 'بیوگرافی',
            'specialties': 'تخصص‌ها',
            'hourly_rate': 'نرخ ساعتی (تومان)',
        }


class CustomPasswordResetForm(EnhancedValidationMixin, PasswordResetForm):
    """Enhanced password reset form with security features"""
    
    email = forms.EmailField(
        label='آدرس ایمیل',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ایمیل خود را وارد کنید',
            'autocomplete': 'email',
            'data-validation': 'email',
            'required': True
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        
        if not email:
            raise ValidationError('آدرس ایمیل الزامی است.')
        
        # Check if user exists
        if not User.objects.filter(email=email).exists():
            # Don't reveal if email exists or not for security
            logger.warning(f'Password reset attempted for non-existent email: {email}')
            return email
        
        # Rate limiting for password reset
        if self.check_rate_limit(email, 'password_reset', limit=3, window_minutes=15):
            raise ValidationError('تعداد درخواست‌های شما زیاد است. لطفاً ۱۵ دقیقه صبر کنید.')
        
        return email


class CustomSetPasswordForm(EnhancedValidationMixin, SetPasswordForm):
    """Enhanced set password form for password reset"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Enhanced password fields
        self.fields['new_password1'].help_text = (
            "رمز عبور جدید باید حداقل ۸ کاراکتر باشد"
        )
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'رمز عبور جدید',
            'autocomplete': 'new-password',
            'data-validation': 'password',
            'data-strength-meter': 'true'
        })
        
        self.fields['new_password2'].help_text = "رمز عبور جدید را مجدداً وارد کنید"
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'تکرار رمز عبور جدید',
            'autocomplete': 'new-password',
            'data-validation': 'password-confirm',
            'data-match': 'new_password1'
        })
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        
        if password:
            if len(password) < 8:
                raise ValidationError('رمز عبور باید حداقل ۸ کاراکتر باشد.')
        
        return password 