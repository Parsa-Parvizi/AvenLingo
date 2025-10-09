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
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام خود را وارد کنید',
            'autocomplete': 'off',
            'required': True,
            'data-validation': 'name',
            'data-realtime': 'true'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        label='نام خانوادگی',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام خانوادگی خود را وارد کنید',
            'autocomplete': 'off',
            'required': True,
            'data-validation': 'name',
            'data-realtime': 'true'
        })
    )
    
    email = forms.EmailField(
        label='آدرس ایمیل',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@email.com',
            'autocomplete': 'off',
            'required': True,
            'data-validation': 'email',
            'data-realtime': 'true',
            'data-check-availability': 'true'
        })
    )
    
    password1 = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور خود را وارد کنید',
            'autocomplete': 'new-password',
            'required': True,
            'data-validation': 'password',
            'data-strength-meter': 'true',
            'minlength': '8'
        }),
        help_text='رمز عبور باید حداقل ۸ کاراکتر باشد و شامل حروف و اعداد باشد.'
    )
    
    password2 = forms.CharField(
        label='تایید رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور خود را مجدد وارد کنید',
            'autocomplete': 'new-password',
            'required': True,
            'data-validation': 'password-confirm',
            'data-match-field': 'id_password1'
        })
    )
    
    # Student profile fields
    phone_number = forms.CharField(
        max_length=20,
        label='شماره تلفن',
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '09123456789',
            'autocomplete': 'off',
            'data-validation': 'phone',
            'inputmode': 'tel',
            'required': True
        })
    )
    
    date_of_birth = forms.DateField(
        label='تاریخ تولد (اختیاری)',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'data-validation': 'date'
        })
    )
    
    english_level = forms.ChoiceField(
        label='سطح زبان انگلیسی',
        choices=[
            ('', 'سطح خود را انتخاب کنید'),
            ('beginner', 'مبتدی'),
            ('elementary', 'پایه'),
            ('intermediate', 'متوسط'),
            ('upper_intermediate', 'متوسط به بالا'),
            ('advanced', 'پیشرفته')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    learning_goals = forms.MultipleChoiceField(
        label='اهداف یادگیری (اختیاری)',
        choices=[
            ('speaking', 'بهبود مکالمه'),
            ('listening', 'بهبود شنیداری'),
            ('reading', 'بهبود خواندن'),
            ('writing', 'بهبود نوشتن'),
            ('grammar', 'یادگیری گرامر'),
            ('vocabulary', 'افزایش واژگان'),
            ('exam_prep', 'آماده‌سازی برای آزمون'),
            ('business', 'انگلیسی تجاری'),
            ('academic', 'انگلیسی آکادمیک'),
        ],
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        })
    )
    
    # Terms and privacy (optional - can be added to template if needed)
    terms_accepted = forms.BooleanField(
        label='قوانین و مقررات را مطالعه کرده و می‌پذیرم',
        required=False,  # Changed to optional since it's not in template
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'required': False
        })
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Add CSS classes and improve help text
        for field_name, field in self.fields.items():
            if field_name not in ['learning_goals', 'terms_accepted']:
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        
        if User.objects.filter(email=email).exists():
            raise ValidationError('این ایمیل قبلاً ثبت شده است. آیا قبلاً حساب کاربری دارید؟')
        
        # Check if this email has a pending teacher application
        if TeacherApplication.objects.for_email(email).exists():
            raise ValidationError('این ایمیل برای درخواست همکاری معلم استفاده شده است.')
        
        return email
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        
        if not phone:
            raise ValidationError('شماره تلفن الزامی است.')
        
        # Basic Iranian phone number validation
        import re
        pattern = r'^09\d{9}$'
        if not re.match(pattern, phone):
            raise ValidationError('شماره تلفن باید با ۰۹ شروع شده و ۱۱ رقم باشد.')
        
        return phone
    
    def check_security(self):
        """Basic security checks for registration"""
        if not self.request:
            return True
        
        # Check rate limiting - allow up to 3 registration attempts per 10 minutes
        user_identifier = self.request.META.get('REMOTE_ADDR', 'unknown')
        if self.check_rate_limit(user_identifier, action_type='registration', limit=5, window_minutes=10):
            return False
        
        return True
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Additional security and validation checks
        if self.request:
            # Check for suspicious activity
            if not self.check_security():
                raise ValidationError('تعداد تلاش‌های ثبت‌نام بیش از حد مجاز است. لطفاً چند دقیقه صبر کنید.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save user and create student profile using service layer"""
        if not commit:
            return super().save(commit=False)
        
        try:
            from .services import UserRegistrationService
            
            # Prepare profile data
            profile_data = {
                'phone_number': self.cleaned_data.get('phone_number', ''),
                'date_of_birth': self.cleaned_data.get('date_of_birth'),
                'english_level': self.cleaned_data.get('english_level', ''),
                'goals': ', '.join(self.cleaned_data.get('learning_goals', []))
            }
            
            # Use service to register student
            user = UserRegistrationService.register_student(
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password1'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                **profile_data
            )
            
            return user
            
        except Exception as e:
            logger.error(f"Error in student registration form save: {str(e)}")
            raise ValidationError('خطا در ثبت‌نام. لطفاً دوباره تلاش کنید.')


class TeacherApplicationForm(EnhancedValidationMixin, forms.ModelForm):
    """Enhanced form for teacher collaboration requests"""
    
    class Meta:
        model = TeacherApplication
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'education', 'experience', 'certifications', 'specialties',
            'motivation', 'cv_file'
        ]
        
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی', 
            'email': 'آدرس ایمیل',
            'phone_number': 'شماره تلفن',
            'education': 'تحصیلات',
            'experience': 'تجربه تدریس',
            'certifications': 'گواهینامه‌ها و مدارک',
            'specialties': 'تخصص‌ها و مهارت‌ها',
            'motivation': 'انگیزه همکاری',
            'cv_file': 'فایل رزومه (PDF)'
        }
        
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام خود را وارد کنید',
                'autocomplete': 'given-name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام خانوادگی خود را وارد کنید',
                'autocomplete': 'family-name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@email.com',
                'autocomplete': 'email'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '09123456789',
                'inputmode': 'tel'
            }),
            'education': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'مدرک تحصیلی، رشته تحصیلی، دانشگاه و سال فارغ‌التحصیلی خود را شرح دهید'
            }),
            'experience': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'تجربه تدریس زبان انگلیسی، محل کار و مدت زمان فعالیت خود را بیان کنید'
            }),
            'certifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'گواهینامه‌های زبان انگلیسی، دوره‌های آموزشی و مدارک مرتبط (اختیاری)'
            }),
            'specialties': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'تخصص‌ها مثل: مکالمه، گرامر، آیلتس، تافل، انگلیسی تجاری و...'
            }),
            'motivation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'چرا می‌خواهید در آکادمی ما تدریس کنید؟ اهداف و انگیزه‌های خود را بیان کنید'
            }),
            'cv_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf',
                'data-max-size': '5120'  # 5MB in KB
            })
        }
        
        help_texts = {
            'cv_file': 'فایل PDF حداکثر ۵ مگابایت',
            'certifications': 'در صورت نداشتن گواهینامه، این قسمت را خالی بگذارید',
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Mark required fields
        required_fields = ['first_name', 'last_name', 'email', 'phone_number', 
                          'education', 'experience', 'specialties', 'motivation']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True
                
        # Add asterisk to required field labels
        for field_name, field in self.fields.items():
            if field.required:
                field.label = f"{field.label} *"
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        
        # Check if application already exists
        if TeacherApplication.objects.for_email(email).exists():
            raise ValidationError('درخواست همکاری با این ایمیل قبلاً ثبت شده است.')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise ValidationError('کاربری با این ایمیل قبلاً در سیستم ثبت شده است.')
        
        return email
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '').strip()
        if phone:
            import re
            pattern = r'^09\d{9}$'
            if not re.match(pattern, phone):
                raise ValidationError('شماره تلفن باید با ۰۹ شروع شده و ۱۱ رقم باشد.')
        return phone
    
    def clean_cv_file(self):
        cv_file = self.cleaned_data.get('cv_file')
        if cv_file:
            # Check file extension
            if not cv_file.name.lower().endswith('.pdf'):
                raise ValidationError('فقط فایل‌های PDF مجاز هستند.')
            
            # Check file size (5MB)
            if cv_file.size > 5 * 1024 * 1024:
                raise ValidationError('حجم فایل نباید بیشتر از ۵ مگابایت باشد.')
            
            # Basic PDF validation
            if cv_file.read(4) != b'%PDF':
                raise ValidationError('فایل آپلود شده معتبر نیست.')
            cv_file.seek(0)  # Reset file pointer
        
        return cv_file
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Security checks
        if self.request and not self.check_security():
            raise ValidationError('خطای امنیتی تشخیص داده شد.')
        
        # Business logic validation
        education = cleaned_data.get('education', '')
        experience = cleaned_data.get('experience', '')
        
        if len(education) < 50:
            raise ValidationError('لطفاً تحصیلات خود را با جزئیات بیشتری شرح دهید.')
        
        if len(experience) < 50:
            raise ValidationError('لطفاً تجربه تدریس خود را با جزئیات بیشتری بیان کنید.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save application using service layer"""
        if not commit:
            return super().save(commit=False)
        
        try:
            from .services import TeacherApplicationService
            
            application = TeacherApplicationService.submit_application(**self.cleaned_data)
            return application
            
        except Exception as e:
            logger.error(f"Error in teacher application form save: {str(e)}")
            raise ValidationError('خطا در ثبت درخواست. لطفاً دوباره تلاش کنید.')


class TeacherRegistrationForm(UserCreationForm):
    """Enhanced registration form for approved teachers"""
    
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
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور خود را وارد کنید',
            'autocomplete': 'new-password',
            'data-validation': 'password',
            'minlength': '8'
        }),
        help_text='رمز عبور باید حداقل ۸ کاراکتر باشد.'
    )
    password2 = forms.CharField(
        label='تایید رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور خود را مجدد وارد کنید',
            'autocomplete': 'new-password',
            'data-validation': 'password-confirm'
        })
    )
    
    bio = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'درباره خود، روش تدریس و تجربیات خود بنویسید...'
        }),
        label='بیوگرافی',
        required=False,
        help_text='این متن در پروفایل عمومی شما نمایش داده خواهد شد.'
    )
    
    hourly_rate = forms.DecimalField(
        label='نرخ ساعتی (تومان)',
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '500000',
            'min': '0',
            'step': '10000'
        }),
        help_text='نرخ تدریس خود را به تومان وارد کنید (اختیاری)'
    )
    
    telegram_username = forms.CharField(
        label='نام کاربری تلگرام',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '@username',
            'pattern': '^@?[a-zA-Z0-9_]{5,32}$'
        }),
        help_text='برای ارتباط با دانش‌آموزان (اختیاری)'
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
        
        if not self.application.can_create_teacher_account():
            raise ValidationError('درخواست شما منقضی شده یا قابل استفاده نیست.')
        
        return email
    
    def clean_telegram_username(self):
        username = self.cleaned_data.get('telegram_username', '').strip()
        if username:
            if not username.startswith('@'):
                username = f'@{username}'
            
            import re
            if not re.match(r'^@[a-zA-Z0-9_]{5,32}$', username):
                raise ValidationError('نام کاربری تلگرام معتبر نیست.')
        
        return username
    
    def save(self, commit=True):
        """Save teacher using service layer"""
        if not commit:
            return super().save(commit=False)
        
        try:
            from .services import UserRegistrationService
            
            # Prepare profile data
            profile_data = {
                'bio': self.cleaned_data.get('bio', ''),
                'hourly_rate': self.cleaned_data.get('hourly_rate'),
                'telegram_username': self.cleaned_data.get('telegram_username', '')
            }
            
            user = UserRegistrationService.register_teacher_from_application(
                application=self.application,
                password=self.cleaned_data['password1'],
                **profile_data
            )
            
            return user
            
        except Exception as e:
            logger.error(f"Error in teacher registration form save: {str(e)}")
            raise ValidationError('خطا در ثبت‌نام معلم. لطفاً دوباره تلاش کنید.')


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


class StudentProfileForm(forms.ModelForm):
    """Form for updating student profile"""
    
    ENGLISH_LEVEL_CHOICES = [
        ('', 'سطح خود را انتخاب کنید'),
        ('beginner', 'مبتدی'),
        ('elementary', 'پایه'),
        ('intermediate', 'متوسط'),
        ('upper_intermediate', 'متوسط به بالا'),
        ('advanced', 'پیشرفته'),
    ]
    
    english_level = forms.ChoiceField(
        choices=ENGLISH_LEVEL_CHOICES,
        required=False,
        label='سطح زبان انگلیسی',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Student
        fields = ['phone_number', 'date_of_birth', 'address', 'english_level', 'goals']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '09123456789'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'آدرس محل سکونت خود را وارد کنید'
            }),
            'goals': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'اهداف یادگیری خود را توضیح دهید'
            }),
        }
        labels = {
            'phone_number': 'شماره تلفن',
            'date_of_birth': 'تاریخ تولد',
            'address': 'آدرس',
            'goals': 'اهداف یادگیری',
        }


class TeacherProfileForm(forms.ModelForm):
    """Form for updating teacher profile"""
    
    # User fields
    first_name = forms.CharField(
        label='نام',
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='نام خانوادگی',
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Teacher
        fields = [
            'bio', 'specialties', 'date_of_birth',
            'telegram_username', 'whatsapp_number', 'instagram_username', 'linkedin_username', 'youtube_username',
            'education_level', 'education_field', 'education_institution',
            'experience_years', 'experience_description',
            'availability_days', 'availability_hours'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'درباره خود، تجربه‌تان و روش تدریس خود بنویسید...'
            }),
            'specialties': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'تخصص‌ها و مهارت‌های خود را با کاما جدا کنید...'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'YYYY-MM-DD'
            }),
            'telegram_username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@username'
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '09123456789'
            }),
            'instagram_username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@username'
            }),
            'linkedin_username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@username یا URL پروفایل'
            }),
            'youtube_username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@username'
            }),
            'education_level': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: کارشناسی، کارشناسی ارشد، دکتری'
            }),
            'education_field': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: زبان انگلیسی، آموزش زبان'
            }),
            'education_institution': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام دانشگاه یا موسسه'
            }),
            'experience_years': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '50'
            }),
            'experience_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'توضیحات تجربه تدریس خود...'
            }),
            'availability_days': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'روزهای هفته که در دسترس هستید...'
            }),
            'availability_hours': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'ساعات روز که در دسترس هستید...'
            }),
        }
        labels = {
            'bio': 'بیوگرافی',
            'specialties': 'تخصص‌ها',
            'date_of_birth': 'تاریخ تولد (اختیاری)',
            'telegram_username': 'نام کاربری تلگرام',
            'whatsapp_number': 'شماره واتساپ',
            'instagram_username': 'نام کاربری اینستاگرام',
            'linkedin_username': 'نام کاربری لینکدین',
            'youtube_username': 'نام کاربری یوتیوب',
            'education_level': 'سطح تحصیلات',
            'education_field': 'رشته تحصیلات',
            'education_institution': 'موسسه تحصیلات',
            'experience_years': 'سال تجربه تدریس',
            'experience_description': 'توضیحات تجربه',
            'availability_days': 'روزهای فعالیت',
            'availability_hours': 'ساعات فعالیت',
        }
        help_texts = {
            'date_of_birth': 'فرمت: سال-ماه-روز (مثال: 1990-01-15) - این فیلد اختیاری است',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initialize user fields with current values
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
        
        # Make date_of_birth optional and add help text
        self.fields['date_of_birth'].required = False
        self.fields['date_of_birth'].widget.attrs.update({
            'placeholder': 'مثال: 1990-01-15'
        })
    
    def clean_bio(self):
        """اعتبارسنجی بیوگرافی"""
        bio = self.cleaned_data.get('bio', '').strip()
        if bio and len(bio) < 50:
            raise ValidationError('بیوگرافی باید حداقل 50 کاراکتر باشد.')
        return bio
    
    def clean_specialties(self):
        """اعتبارسنجی تخصص‌ها"""
        specialties = self.cleaned_data.get('specialties', '').strip()
        if specialties and len(specialties) < 10:
            raise ValidationError('تخصص‌ها باید حداقل 10 کاراکتر باشد.')
        return specialties
    
    
    def clean_date_of_birth(self):
        """اعتبارسنجی تاریخ تولد"""
        date_of_birth = self.cleaned_data.get('date_of_birth')
        
        # اگر خالی است، مشکلی نیست
        if not date_of_birth:
            return None
        
        # بررسی که تاریخ در گذشته باشد
        from django.utils import timezone
        if date_of_birth > timezone.now().date():
            raise ValidationError('تاریخ تولد نمی‌تواند در آینده باشد.')
        
        # بررسی که شخص بالای 15 سال باشد
        age = (timezone.now().date() - date_of_birth).days / 365.25
        if age < 15:
            raise ValidationError('سن باید حداقل 15 سال باشد.')
        
        if age > 100:
            raise ValidationError('لطفاً تاریخ تولد صحیح وارد کنید.')
        
        return date_of_birth
    
    def clean_whatsapp_number(self):
        """اعتبارسنجی شماره واتساپ"""
        whatsapp = self.cleaned_data.get('whatsapp_number', '').strip()
        if whatsapp:
            # حذف کاراکترهای غیرعددی
            whatsapp_clean = ''.join(filter(str.isdigit, whatsapp))
            if len(whatsapp_clean) < 10 or len(whatsapp_clean) > 15:
                raise ValidationError('شماره واتساپ باید بین 10 تا 15 رقم باشد.')
            return whatsapp_clean
        return whatsapp
    
    def clean_youtube_username(self):
        """اعتبارسنجی نام کاربری یوتیوب"""
        youtube = self.cleaned_data.get('youtube_username', '').strip()
        if youtube:
            # حذف @ اگر وجود دارد
            if youtube.startswith('@'):
                youtube = youtube[1:]
            
            # فقط حذف فاصله‌های اضافی - validation خیلی ساده
            return youtube.strip()
        return ''
    
    def save(self, commit=True):
        """ذخیره پروفایل معلم با به‌روزرسانی اطلاعات کاربر"""
        teacher = super().save(commit=False)
        
        # به‌روزرسانی اطلاعات کاربر
        if teacher.user:
            teacher.user.first_name = self.cleaned_data.get('first_name', '')
            teacher.user.last_name = self.cleaned_data.get('last_name', '')
            teacher.user.save(update_fields=['first_name', 'last_name'])
        
        if commit:
            teacher.save()
        
        return teacher


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