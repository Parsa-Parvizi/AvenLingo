from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Course, Assignment, AssignmentSubmission, Exam, ExamParticipation
from datetime import datetime
import re

# Try to import jdatetime, with fallback
try:
    import jdatetime
    JDATETIME_AVAILABLE = True
except ImportError:
    JDATETIME_AVAILABLE = False
    print("⚠️  Warning: jdatetime not available. Persian date conversion disabled.")


def persian_to_gregorian_date(persian_date_str):
    """تبدیل تاریخ شمسی به میلادی"""
    if not persian_date_str or not JDATETIME_AVAILABLE:
        return None
    
    try:
        # فرمت: 1403/07/15 یا ۱۴۰۳/۰۷/۱۵
        # ابتدا اعداد فارسی را به انگلیسی تبدیل می‌کنیم
        persian_nums = '۰۱۲۳۴۵۶۷۸۹'
        english_nums = '0123456789'
        trans_table = str.maketrans(persian_nums, english_nums)
        date_str = persian_date_str.translate(trans_table)
        
        # حذف کاراکترهای اضافی
        date_str = re.sub(r'[^\d/]', '', date_str)
        
        # تبدیل به تاریخ میلادی
        parts = date_str.split('/')
        if len(parts) == 3:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            j_date = jdatetime.date(year, month, day)
            return j_date.togregorian()
    except:
        pass
    
    return None


def persian_to_gregorian_datetime(persian_datetime_str):
    """تبدیل تاریخ و ساعت شمسی به میلادی"""
    if not persian_datetime_str or not JDATETIME_AVAILABLE:
        return None
    
    try:
        # فرمت: 1403/07/15 14:30 یا ۱۴۰۳/۰۷/۱۵ ۱۴:۳۰
        persian_nums = '۰۱۲۳۴۵۶۷۸۹'
        english_nums = '0123456789'
        trans_table = str.maketrans(persian_nums, english_nums)
        datetime_str = persian_datetime_str.translate(trans_table).strip()
        
        # جدا کردن تاریخ و ساعت
        parts = datetime_str.split(' ')
        
        if len(parts) >= 1:
            # پردازش تاریخ
            date_parts = parts[0].split('/')
            if len(date_parts) == 3:
                year, month, day = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
                
                # پردازش ساعت (اگر وجود داشته باشد)
                hour, minute = 0, 0
                if len(parts) >= 2:
                    time_parts = parts[1].split(':')
                    if len(time_parts) >= 2:
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                
                # تبدیل به datetime میلادی
                j_datetime = jdatetime.datetime(year, month, day, hour, minute)
                return timezone.make_aware(j_datetime.togregorian())
    except:
        pass
    
    return None


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        exclude = [
            'teacher', 'students', 'enrolled_count', 'slug', 'is_active', 'is_featured', 'created_at', 'updated_at', 'status'
        ]
        widgets = {
            'start_date': forms.TextInput(attrs={
                'class': 'form-control persian-date',
                'placeholder': 'روز/ماه/سال (مثال: ۱۴۰۳/۰۷/۱۵)',
                'autocomplete': 'off'
            }),
            'end_date': forms.TextInput(attrs={
                'class': 'form-control persian-date',
                'placeholder': 'روز/ماه/سال (مثال: ۱۴۰۳/۱۰/۱۵)',
                'autocomplete': 'off'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['start_date', 'end_date']:
                field.widget.attrs['class'] = 'form-control'
        
        # اگر در حال ویرایش است، تاریخ‌ها را به شمسی تبدیل کن
        if JDATETIME_AVAILABLE and self.instance and self.instance.pk:
            if self.instance.start_date:
                try:
                    j_date = jdatetime.date.fromgregorian(date=self.instance.start_date)
                    self.initial['start_date'] = j_date.strftime('%Y/%m/%d')
                except:
                    pass
            
            if self.instance.end_date:
                try:
                    j_date = jdatetime.date.fromgregorian(date=self.instance.end_date)
                    self.initial['end_date'] = j_date.strftime('%Y/%m/%d')
                except:
                    pass
    
    def clean_start_date(self):
        """تبدیل تاریخ شمسی به میلادی"""
        start_date_str = self.cleaned_data.get('start_date')
        
        # اگر string است، تبدیل کن
        if isinstance(start_date_str, str):
            gregorian_date = persian_to_gregorian_date(start_date_str)
            if gregorian_date:
                return gregorian_date
            else:
                raise ValidationError('فرمت تاریخ صحیح نیست. از فرمت YYYY/MM/DD استفاده کنید.')
        
        return start_date_str
    
    def clean_end_date(self):
        """تبدیل تاریخ شمسی به میلادی"""
        end_date_str = self.cleaned_data.get('end_date')
        
        if not end_date_str:
            return None
        
        # اگر string است، تبدیل کن
        if isinstance(end_date_str, str):
            gregorian_date = persian_to_gregorian_date(end_date_str)
            if gregorian_date:
                return gregorian_date
            else:
                raise ValidationError('فرمت تاریخ صحیح نیست. از فرمت YYYY/MM/DD استفاده کنید.')
        
        return end_date_str


class AssignmentForm(forms.ModelForm):
    """فرم ایجاد و ویرایش تکلیف توسط معلم"""
    
    class Meta:
        model = Assignment
        fields = [
            'title', 'description', 'assignment_type', 'instruction_file',
            'due_date', 'late_submission_allowed', 'late_submission_penalty',
            'total_points', 'passing_score', 'allow_multiple_submissions',
            'auto_grade', 'additional_instructions', 'grading_criteria'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان تکلیف را وارد کنید'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'توضیحات تکلیف را بنویسید'
            }),
            'assignment_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'due_date': forms.TextInput(attrs={
                'class': 'form-control persian-datetime',
                'placeholder': 'روز/ماه/سال ساعت:دقیقه',
                'autocomplete': 'off'
            }),
            'late_submission_penalty': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'جریمه ارسال دیر هنگام (اختیاری)'
            }),
            'total_points': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '1000'
            }),
            'passing_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'additional_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'دستورالعمل‌های اضافی (اختیاری)'
            }),
            'grading_criteria': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'معیارهای ارزیابی (اختیاری)'
            }),
            'instruction_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.rtf'
            }),
        }
        
        labels = {
            'title': 'عنوان تکلیف',
            'description': 'توضیحات تکلیف',
            'assignment_type': 'نوع تکلیف',
            'instruction_file': 'فایل دستورالعمل',
            'due_date': 'مهلت ارسال',
            'late_submission_allowed': 'اجازه ارسال دیر هنگام',
            'late_submission_penalty': 'جریمه ارسال دیر هنگام',
            'total_points': 'مجموع امتیاز',
            'passing_score': 'نمره قبولی',
            'allow_multiple_submissions': 'اجازه ارسال چندگانه',
            'auto_grade': 'نمره‌دهی خودکار',
            'additional_instructions': 'دستورالعمل‌های اضافی',
            'grading_criteria': 'معیارهای ارزیابی',
        }
    
    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        
        # اگر در حال ویرایش است، due_date را به شمسی تبدیل کن
        if JDATETIME_AVAILABLE and self.instance and self.instance.pk and self.instance.due_date:
            try:
                j_datetime = jdatetime.datetime.fromgregorian(datetime=self.instance.due_date)
                self.initial['due_date'] = j_datetime.strftime('%Y/%m/%d %H:%M')
            except:
                pass
    
    def clean_due_date(self):
        """اعتبارسنجی و تبدیل تاریخ شمسی به میلادی"""
        due_date = self.cleaned_data.get('due_date')
        
        # اگر string است، تبدیل به datetime میلادی
        if isinstance(due_date, str):
            gregorian_datetime = persian_to_gregorian_datetime(due_date)
            if gregorian_datetime:
                due_date = gregorian_datetime
            else:
                raise ValidationError('فرمت تاریخ و ساعت صحیح نیست. مثال: 1403/07/15 14:30')
        
        if due_date:
            # مهلت ارسال باید حداقل 1 ساعت از الان باشد
            min_datetime = timezone.now() + timezone.timedelta(hours=1)
            if due_date < min_datetime:
                raise ValidationError('مهلت ارسال باید حداقل 1 ساعت از الان باشد.')
        
        return due_date
    
    def clean_passing_score(self):
        """اعتبارسنجی نمره قبولی"""
        passing_score = self.cleaned_data.get('passing_score')
        total_points = self.cleaned_data.get('total_points')
        
        if passing_score and total_points:
            if passing_score > total_points:
                raise ValidationError('نمره قبولی نمی‌تواند بیشتر از مجموع امتیاز باشد.')
        
        return passing_score
    
    def save(self, commit=True):
        """ذخیره تکلیف با تنظیم معلم و دوره"""
        assignment = super().save(commit=False)
        
        if self.teacher:
            assignment.teacher = self.teacher
        if self.course:
            assignment.course = self.course
        
        if commit:
            assignment.save()
        
        return assignment


class AssignmentSubmissionForm(forms.ModelForm):
    """فرم ارسال تکلیف توسط دانش‌آموز"""
    
    class Meta:
        model = AssignmentSubmission
        fields = ['submission_file', 'additional_files', 'text_content', 'comments']
        
        widgets = {
            'submission_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.rtf,.zip,.rar',
                'required': True
            }),
            'additional_files': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.rtf,.zip,.rar,.jpg,.jpeg,.png'
            }),
            'text_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'محتوای متنی تکلیف خود را اینجا بنویسید (اختیاری)'
            }),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'توضیحات یا سوالات خود را اینجا بنویسید (اختیاری)'
            }),
        }
        
        labels = {
            'submission_file': 'فایل تکلیف *',
            'additional_files': 'فایل‌های اضافی',
            'text_content': 'محتوای متنی',
            'comments': 'توضیحات',
        }
    
    def __init__(self, *args, **kwargs):
        self.assignment = kwargs.pop('assignment', None)
        self.student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        
        # اگر تکلیف قبلاً ارسال شده و اجازه ارسال چندگانه نیست
        if self.assignment and self.student:
            existing_submission = AssignmentSubmission.objects.filter(
                assignment=self.assignment,
                student=self.student
            ).first()
            
            if existing_submission and not self.assignment.allow_multiple_submissions:
                self.fields['submission_file'].widget.attrs['disabled'] = True
                self.fields['text_content'].widget.attrs['readonly'] = True
                self.fields['comments'].widget.attrs['readonly'] = True
    
    def clean_submission_file(self):
        """اعتبارسنجی فایل ارسالی"""
        submission_file = self.cleaned_data.get('submission_file')
        
        if submission_file:
            # بررسی حجم فایل (حداکثر 10MB)
            max_size = 10 * 1024 * 1024  # 10MB
            if submission_file.size > max_size:
                raise ValidationError('حجم فایل نباید بیشتر از 10 مگابایت باشد.')
            
            # بررسی نوع فایل
            allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.zip', '.rar']
            file_extension = submission_file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise ValidationError('نوع فایل مجاز نیست. فایل‌های مجاز: PDF, DOC, DOCX, TXT, RTF, ZIP, RAR')
        
        return submission_file
    
    def clean(self):
        """اعتبارسنجی کلی فرم"""
        cleaned_data = super().clean()
        submission_file = cleaned_data.get('submission_file')
        text_content = cleaned_data.get('text_content')
        
        # حداقل یکی از فایل یا محتوای متنی باید ارائه شود
        if not submission_file and not text_content:
            raise ValidationError('لطفاً فایل تکلیف یا محتوای متنی را ارائه دهید.')
        
        return cleaned_data
    
    def save(self, commit=True):
        """ذخیره ارسال تکلیف با تنظیم دانش‌آموز و تکلیف"""
        submission = super().save(commit=False)
        
        if self.assignment:
            submission.assignment = self.assignment
        if self.student:
            submission.student = self.student
        
        # تنظیم شماره تلاش
        if self.assignment and self.student:
            existing_submissions = AssignmentSubmission.objects.filter(
                assignment=self.assignment,
                student=self.student
            ).count()
            submission.attempt_number = existing_submissions + 1
        
        if commit:
            submission.save()
        
        return submission


class AssignmentGradingForm(forms.ModelForm):
    """فرم نمره‌دهی تکلیف توسط معلم"""
    
    class Meta:
        model = AssignmentSubmission
        fields = ['score', 'feedback']
        
        widgets = {
            'score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '1000',
                'step': '0.1'
            }),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'بازخورد خود را برای دانش‌آموز بنویسید...'
            }),
        }
        
        labels = {
            'score': 'نمره',
            'feedback': 'بازخورد',
        }
    
    def __init__(self, *args, **kwargs):
        self.assignment = kwargs.pop('assignment', None)
        super().__init__(*args, **kwargs)
        
        # تنظیم حداکثر نمره بر اساس تکلیف
        if self.assignment:
            self.fields['score'].widget.attrs['max'] = self.assignment.total_points
    
    def clean_score(self):
        """اعتبارسنجی نمره"""
        score = self.cleaned_data.get('score')
        
        if score is not None:
            if self.assignment and score > self.assignment.total_points:
                raise ValidationError(f'نمره نمی‌تواند بیشتر از {self.assignment.total_points} باشد.')
            
            if score < 0:
                raise ValidationError('نمره نمی‌تواند منفی باشد.')
        
        return score

class ExamForm(forms.ModelForm):
    """فرم ایجاد و ویرایش امتحان توسط معلم"""
    
    class Meta:
        model = Exam
        fields = [
            'title', 'description', 'exam_type', 'question_file', 'instructions',
            'scheduled_start', 'scheduled_end', 'duration_minutes',
            'is_visible', 'visibility_date',
            'total_points', 'passing_score', 'auto_close', 'allow_late_submission', 'late_penalty_percent',
            'randomize_questions', 'show_answers_after', 'max_attempts'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان امتحان'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'exam_type': forms.Select(attrs={'class': 'form-control'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'scheduled_start': forms.TextInput(attrs={'class': 'form-control persian-datetime', 'placeholder': 'روز/ماه/سال ساعت:دقیقه'}),
            'scheduled_end': forms.TextInput(attrs={'class': 'form-control persian-datetime', 'placeholder': 'روز/ماه/سال ساعت:دقیقه'}),
            'visibility_date': forms.TextInput(attrs={'class': 'form-control persian-datetime', 'placeholder': 'روز/ماه/سال ساعت:دقیقه'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'total_points': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'passing_score': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'late_penalty_percent': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100'}),
            'max_attempts': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'value': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        
        # تبدیل تاریخ‌ها به شمسی برای ویرایش
        if JDATETIME_AVAILABLE and self.instance and self.instance.pk:
            for field_name in ['scheduled_start', 'scheduled_end', 'visibility_date']:
                field_value = getattr(self.instance, field_name, None)
                if field_value:
                    try:
                        j_datetime = jdatetime.datetime.fromgregorian(datetime=field_value)
                        self.initial[field_name] = j_datetime.strftime('%Y/%m/%d %H:%M')
                    except:
                        pass
    
    def clean_scheduled_start(self):
        """تبدیل تاریخ شمسی به میلادی"""
        scheduled_start = self.cleaned_data.get('scheduled_start')
        if isinstance(scheduled_start, str):
            gregorian_datetime = persian_to_gregorian_datetime(scheduled_start)
            if gregorian_datetime:
                return gregorian_datetime
            raise ValidationError('فرمت تاریخ صحیح نیست')
        return scheduled_start
    
    def clean_scheduled_end(self):
        """تبدیل تاریخ شمسی به میلادی"""
        scheduled_end = self.cleaned_data.get('scheduled_end')
        if isinstance(scheduled_end, str):
            gregorian_datetime = persian_to_gregorian_datetime(scheduled_end)
            if gregorian_datetime:
                return gregorian_datetime
            raise ValidationError('فرمت تاریخ صحیح نیست')
        return scheduled_end
    
    def clean_visibility_date(self):
        """تبدیل تاریخ شمسی به میلادی"""
        visibility_date = self.cleaned_data.get('visibility_date')
        if not visibility_date:
            return None
        if isinstance(visibility_date, str):
            gregorian_datetime = persian_to_gregorian_datetime(visibility_date)
            if gregorian_datetime:
                return gregorian_datetime
            raise ValidationError('فرمت تاریخ صحیح نیست')
        return visibility_date
    
    def clean(self):
        cleaned_data = super().clean()
        scheduled_start = cleaned_data.get('scheduled_start')
        scheduled_end = cleaned_data.get('scheduled_end')
        
        if scheduled_start and scheduled_end:
            if scheduled_end <= scheduled_start:
                raise ValidationError('زمان پایان باید بعد از زمان شروع باشد')
        
        return cleaned_data
    
    def save(self, commit=True):
        exam = super().save(commit=False)
        
        if self.teacher:
            exam.teacher = self.teacher
        if self.course:
            exam.course = self.course
        
        if commit:
            exam.save()
        
        return exam
