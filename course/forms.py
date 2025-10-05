from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Course, Assignment, AssignmentSubmission

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        exclude = [
            'teacher', 'students', 'enrolled_count', 'slug', 'is_active', 'is_featured', 'created_at', 'updated_at', 'status'
        ]
        # فقط فیلدهای مورد نیاز معلم برای ثبت کلاس را نمایش بده

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


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
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
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
        
        # تنظیم مهلت ارسال حداقل 1 ساعت از الان
        if not self.instance.pk:  # فقط برای تکالیف جدید
            min_datetime = timezone.now() + timezone.timedelta(hours=1)
            self.fields['due_date'].widget.attrs['min'] = min_datetime.strftime('%Y-%m-%dT%H:%M')
    
    def clean_due_date(self):
        """اعتبارسنجی مهلت ارسال"""
        due_date = self.cleaned_data.get('due_date')
        
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