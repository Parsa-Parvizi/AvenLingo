from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import re

from .models import Enrollment
from course.models import Course, LEVEL_CHOICES, AGE_GROUP_CHOICES, CLASS_TYPE_CHOICES
from account.models import Student


def extract_schedule_info(duration_text):
    """
    استخراج اطلاعات زمان‌بندی از متن duration
    برمی‌گرداند: (روزهای هفته، ساعت شروع، ساعت پایان)
    """
    if not duration_text:
        return None, None, None
    
    # نرمال‌سازی متن
    text = duration_text.lower().strip()
    
    # استخراج روزهای هفته (فارسی و انگلیسی)
    # استفاده از word boundary برای جلوگیری از match شدن "شنبه" در "یکشنبه"
    days_map = [
        (r'\bچهارشنبه\b', 'wednesday'),
        (r'\bچهار\s*شنبه\b', 'wednesday'),
        (r'\bپنج‌شنبه\b', 'thursday'),
        (r'\bپنج\s*شنبه\b', 'thursday'),
        (r'\bسه‌شنبه\b', 'tuesday'),
        (r'\bسه\s*شنبه\b', 'tuesday'),
        (r'\bیکشنبه\b', 'sunday'),
        (r'\bدوشنبه\b', 'monday'),
        (r'\bجمعه\b', 'friday'),
        (r'\bشنبه\b', 'saturday'),  # با word boundary، فقط "شنبه" standalone را می‌گیرد
        (r'\bsaturday\b', 'saturday'),
        (r'\bwednesday\b', 'wednesday'),
        (r'\bthursday\b', 'thursday'),
        (r'\btuesday\b', 'tuesday'),
        (r'\bsunday\b', 'sunday'),
        (r'\bmonday\b', 'monday'),
        (r'\bfriday\b', 'friday'),
    ]
    
    found_days = []
    for pattern, day_english in days_map:
        if re.search(pattern, text):
            if day_english not in found_days:
                found_days.append(day_english)
    
    # استخراج ساعات (با پشتیبانی از اعداد فارسی و انگلیسی)
    # تبدیل اعداد فارسی به انگلیسی
    persian_to_english = str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789')
    text = text.translate(persian_to_english)
    
    # الگوهای مختلف برای ساعت
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(?:تا|الی|[-–])\s*(\d{1,2}):(\d{2})',  # 17:00 تا 19:00 (اول چک شود)
        r'ساعت\s*(\d{1,2})\s*(?:تا|الی|[-–])\s*(\d{1,2})',  # ساعت 17 تا 19
        r'(\d{1,2})\s*(?:تا|الی|[-–])\s*(\d{1,2})',  # 17 تا 19 یا 17-19
    ]
    
    start_time = None
    end_time = None
    
    for pattern in time_patterns:
        match = re.search(pattern, text)
        if match:
            groups = match.groups()
            if len(groups) == 4:
                # Format: HH:MM to HH:MM
                start_time = float(groups[0]) + float(groups[1]) / 60
                end_time = float(groups[2]) + float(groups[3]) / 60
            elif len(groups) == 2:
                # Format: HH to HH
                start_time = float(groups[0])
                end_time = float(groups[1])
            break
    
    return found_days, start_time, end_time


def check_time_overlap(duration1, duration2):
    """
    بررسی تداخل زمانی بین دو دوره
    برمی‌گرداند: True اگر تداخل وجود داشته باشد
    """
    days1, start1, end1 = extract_schedule_info(duration1)
    days2, start2, end2 = extract_schedule_info(duration2)
    
    # اگر نتوانستیم زمان را extract کنیم، تداخل نداریم
    if not days1 or not days2 or start1 is None or start2 is None or end1 is None or end2 is None:
        return False
    
    # بررسی تداخل روز
    common_days = set(days1) & set(days2)
    if not common_days:
        return False
    
    # بررسی تداخل ساعت
    # دو بازه زمانی تداخل دارند اگر یکی شروع شود قبل از اینکه دیگری تمام شود
    # و دیگری شروع شود قبل از اینکه یکی تمام شود
    # به عبارت دیگر: start1 < end2 AND start2 < end1
    # اگر دقیقاً مجاور باشند (end1 == start2 یا end2 == start1) تداخل نداریم
    if start1 < end2 and start2 < end1:
        return True
    
    return False


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
            
            # بررسی تداخل زمانی با دوره‌های دیگر دانش‌آموز
            existing_enrollments = Enrollment.objects.filter(
                student=self.student,
                status__in=['pending', 'confirmed']
            ).select_related('course')
            
            for enrollment in existing_enrollments:
                if enrollment.course.duration and self.course.duration:
                    if check_time_overlap(enrollment.course.duration, self.course.duration):
                        # استخراج اطلاعات برای نمایش پیام بهتر
                        days1, start1, end1 = extract_schedule_info(enrollment.course.duration)
                        days2, start2, end2 = extract_schedule_info(self.course.duration)
                        
                        # نام روزهای مشترک به فارسی
                        days_persian = {
                            'saturday': 'شنبه',
                            'sunday': 'یکشنبه',
                            'monday': 'دوشنبه',
                            'tuesday': 'سه‌شنبه',
                            'wednesday': 'چهارشنبه',
                            'thursday': 'پنج‌شنبه',
                            'friday': 'جمعه',
                        }
                        
                        common_days = list(set(days1) & set(days2))
                        common_days_persian = [days_persian.get(d, d) for d in common_days]
                        
                        error_msg = (
                            f'تداخل زمانی با دوره "{enrollment.course.title}" وجود دارد. '
                            f'هر دو دوره در روز(های) {", ".join(common_days_persian)} '
                            f'برگزار می‌شوند و زمان‌بندی آن‌ها با هم تداخل دارد. '
                            f'لطفاً یکی از دوره‌ها را انتخاب کنید.'
                        )
                        raise ValidationError(error_msg)
        
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
        
        # بررسی تداخل زمانی
        if self.student and course.duration:
            existing_enrollments = Enrollment.objects.filter(
                student=self.student,
                status__in=['pending', 'confirmed']
            ).select_related('course')
            
            for enrollment in existing_enrollments:
                if enrollment.course.duration:
                    if check_time_overlap(enrollment.course.duration, course.duration):
                        raise ValidationError(
                            f'تداخل زمانی با دوره "{enrollment.course.title}" وجود دارد. '
                            f'لطفاً یکی از دوره‌ها را انتخاب کنید.'
                        )
        
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
        choices=[('', 'همه سطوح')] + list(LEVEL_CHOICES),
        required=False,
        label="سطح",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class_type = forms.ChoiceField(
        choices=[('', 'همه انواع')] + list(CLASS_TYPE_CHOICES),
        required=False,
        label="نوع کلاس",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    age_group = forms.ChoiceField(
        choices=[('', 'همه گروه‌های سنی')] + list(AGE_GROUP_CHOICES),
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