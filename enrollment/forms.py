from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import re

from .models import Enrollment
from course.models import Course
from account.models import Student


class EnrollmentForm(forms.ModelForm):
    """Enhanced enrollment form with validation"""
    
    terms_accepted = forms.BooleanField(
        required=True,
        label="قوانین و مقررات",
        help_text="شرایط و قوانین آموزشگاه را مطالعه کرده و می‌پذیرم",
        error_messages={
            'required': 'پذیرش قوانین و مقررات الزامی است.'
        }
    )
    
    contact_preference = forms.ChoiceField(
        choices=[
            ('phone', 'تماس تلفنی'),
            ('email', 'ایمیل'),
            ('sms', 'پیامک'),
        ],
        required=False,
        label="روش ارتباط ترجیحی",
        help_text="روش ترجیحی برای ارتباط با شما",
        widget=forms.RadioSelect
    )
    
    emergency_contact_name = forms.CharField(
        max_length=100,
        required=False,
        label="نام شخص ضروری",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام کامل'
        })
    )
    
    emergency_contact_phone = forms.CharField(
        max_length=15,
        required=False,
        label="شماره تماس ضروری",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '09123456789',
            'pattern': r'09\d{9}'
        })
    )
    
    special_needs = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'در صورت داشتن نیازهای خاص یا محدودیت‌هایی، لطفاً اینجا ذکر کنید...'
        }),
        required=False,
        label="نیازهای خاص",
        help_text="محدودیت‌ها، آلرژی‌ها، یا نیازهای خاص"
    )
    
    class Meta:
        model = Enrollment
        fields = ['note', 'payment_receipt']
        widgets = {
            'note': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'توضیحات اضافی در مورد ثبت‌نام شما...'
            }),
            'payment_receipt': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*,.pdf'
            })
        }
        labels = {
            'note': 'توضیحات اضافی',
            'payment_receipt': 'فیش واریزی'
        }
        help_texts = {
            'note': 'انگیزه ثبت‌نام، اهداف یادگیری، یا سایر توضیحات',
            'payment_receipt': 'تصویر یا PDF فیش واریزی (فقط برای دوره‌های غیررایگان)'
        }
    
    def __init__(self, *args, **kwargs):
        self.course = kwargs.pop('course', None)
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        
        # Set course-specific help texts
        if self.course:
            self.fields['note'].help_text = f'توضیحات اضافی برای دوره "{self.course.title}"'
            
            # Hide payment receipt field for free courses
            if self.course.is_free:
                self.fields['payment_receipt'].required = False
                self.fields['payment_receipt'].widget = forms.HiddenInput()
            else:
                self.fields['payment_receipt'].required = True
    
    def clean_emergency_contact_phone(self):
        phone = self.cleaned_data.get('emergency_contact_phone')
        if phone:
            # Validate Iranian mobile number
            if not re.match(r'^09\d{9}$', phone):
                raise ValidationError('شماره تماس باید به فرمت 09123456789 باشد.')
        return phone
    
    def clean_note(self):
        note = self.cleaned_data.get('note', '')
        
        # Check for suspicious content
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'onclick=',
            r'onerror=',
            r'<iframe',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, note, re.IGNORECASE):
                raise ValidationError('محتوای وارد شده مجاز نیست.')
        
        # Length validation
        if len(note) > 1000:
            raise ValidationError('توضیحات نباید بیش از ۱۰۰۰ کاراکتر باشد.')
        
        return note
    
    def clean_payment_receipt(self):
        receipt = self.cleaned_data.get('payment_receipt')
        
        # Only validate if course is not free and receipt is provided
        if self.course and not self.course.is_free and receipt:
            # Check file size (max 5MB)
            if receipt.size > 5 * 1024 * 1024:
                raise ValidationError('حجم فایل نباید بیش از ۵ مگابایت باشد.')
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
            if receipt.content_type not in allowed_types:
                raise ValidationError('فرمت فایل باید JPEG، PNG یا PDF باشد.')
        
        return receipt
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate course availability
        if self.course and self.student:
            # Check if already enrolled
            if Enrollment.objects.filter(
                student=self.student, 
                course=self.course,
                status__in=['pending', 'confirmed']
            ).exists():
                raise ValidationError('شما قبلاً در این دوره ثبت‌نام کرده‌اید.')
            
            # Check course capacity
            if self.course.is_full:
                raise ValidationError('ظرفیت این دوره تکمیل شده است.')
            
            # Check if course is active
            if not self.course.is_active:
                raise ValidationError('این دوره در حال حاضر فعال نیست.')
            
            # Check enrollment deadline (if course has started more than 7 days ago)
            if (self.course.start_date and 
                timezone.now().date() > self.course.start_date + timedelta(days=7)):
                raise ValidationError('مهلت ثبت‌نام در این دوره پایان یافته است.')
        
        # Cross-field validation for emergency contact
        emergency_name = cleaned_data.get('emergency_contact_name')
        emergency_phone = cleaned_data.get('emergency_contact_phone')
        
        if emergency_name and not emergency_phone:
            raise ValidationError('در صورت وارد کردن نام شخص ضروری، شماره تماس نیز الزامی است.')
        
        if emergency_phone and not emergency_name:
            raise ValidationError('در صورت وارد کردن شماره تماس ضروری، نام نیز الزامی است.')
        
        return cleaned_data


class QuickEnrollmentForm(forms.Form):
    """Simple form for quick enrollment via AJAX"""
    
    course_id = forms.IntegerField(widget=forms.HiddenInput())
    
    def __init__(self, *args, **kwargs):
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
    
    def clean_course_id(self):
        course_id = self.cleaned_data.get('course_id')
        
        try:
            course = Course.objects.get(id=course_id, is_active=True)
        except Course.DoesNotExist:
            raise ValidationError('دوره انتخابی یافت نشد.')
        
        # Additional validations
        if course.is_full:
            raise ValidationError('ظرفیت این دوره تکمیل شده است.')
        
        if self.student and Enrollment.objects.filter(
            student=self.student, 
            course=course,
            status__in=['pending', 'confirmed']
        ).exists():
            raise ValidationError('شما قبلاً در این دوره ثبت‌نام کرده‌اید.')
        
        return course_id


class EnrollmentCancellationForm(forms.Form):
    """Form for cancelling enrollment"""
    
    CANCELLATION_REASONS = [
        ('schedule_conflict', 'تداخل زمانی'),
        ('financial_issues', 'مشکلات مالی'),
        ('course_content', 'عدم تطابق محتوای دوره'),
        ('personal_reasons', 'دلایل شخصی'),
        ('health_issues', 'مشکلات سلامتی'),
        ('relocation', 'تغییر محل سکونت'),
        ('other', 'سایر دلایل'),
    ]
    
    reason = forms.ChoiceField(
        choices=CANCELLATION_REASONS,
        required=True,
        label="دلیل لغو",
        widget=forms.RadioSelect
    )
    
    additional_comments = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'placeholder': 'توضیحات اضافی...'
        }),
        required=False,
        label="توضیحات اضافی",
        max_length=500
    )
    
    confirm_cancellation = forms.BooleanField(
        required=True,
        label="تأیید لغو",
        help_text="تأیید می‌کنم که می‌خواهم ثبت‌نام خود را لغو کنم.",
        error_messages={
            'required': 'برای لغو ثبت‌نام باید این گزینه را انتخاب کنید.'
        }
    )
    
    def clean_additional_comments(self):
        comments = self.cleaned_data.get('additional_comments', '')
        
        # Basic content validation
        if len(comments) > 500:
            raise ValidationError('توضیحات نباید بیش از ۵۰۰ کاراکتر باشد.')
        
        # Check for suspicious content
        suspicious_patterns = [r'<script', r'javascript:', r'<iframe']
        for pattern in suspicious_patterns:
            if re.search(pattern, comments, re.IGNORECASE):
                raise ValidationError('محتوای وارد شده مجاز نیست.')
        
        return comments


class CourseFilterForm(forms.Form):
    """Form for filtering available courses"""
    
    level = forms.ChoiceField(
        choices=[('', 'همه سطوح')] + Course.LEVEL_CHOICES,
        required=False,
        label="سطح",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class_type = forms.ChoiceField(
        choices=[('', 'همه انواع')] + Course.CLASS_TYPE_CHOICES,
        required=False,
        label="نوع کلاس",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    age_group = forms.ChoiceField(
        choices=[('', 'همه گروه‌های سنی')] + Course.AGE_GROUP_CHOICES,
        required=False,
        label="گروه سنی",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_online = forms.BooleanField(
        required=False,
        label="فقط کلاس‌های آنلاین",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    is_free = forms.BooleanField(
        required=False,
        label="فقط کلاس‌های رایگان",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    max_price = forms.DecimalField(
        required=False,
        label="حداکثر قیمت",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'تومان'
        })
    )
    
    search = forms.CharField(
        required=False,
        label="جستجو",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'جستجو در عنوان، توضیحات، یا نام مدرس...'
        })
    )
    
    def clean_search(self):
        search = self.cleaned_data.get('search', '')
        
        # Basic validation
        if len(search) > 100:
            raise ValidationError('عبارت جستجو نباید بیش از ۱۰۰ کاراکتر باشد.')
        
        # Remove potentially harmful characters
        search = re.sub(r'[<>"\';]', '', search)
        
        return search.strip() 