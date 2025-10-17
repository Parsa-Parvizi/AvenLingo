from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Course, Assignment, AssignmentSubmission, Exam, ExamParticipation
from datetime import datetime, date
import re

# Try to import jdatetime, with fallback
try:
    import jdatetime
    JDATETIME_AVAILABLE = True
except ImportError:
    jdatetime = None
    JDATETIME_AVAILABLE = False
    print("⚠️  Warning: jdatetime not available. Using manual Persian date conversion.")


def clean_persian_date_string(date_str):
    """پاک‌سازی و استخراج تاریخ از رشته فارسی"""
    if not date_str:
        return None
    
    # تبدیل نام ماه‌های فارسی به عدد
    persian_months = {
        'فروردین': '01', 'اردیبهشت': '02', 'خرداد': '03',
        'تیر': '04', 'مرداد': '05', 'شهریور': '06',
        'مهر': '07', 'آبان': '08', 'آذر': '09',
        'دی': '10', 'بهمن': '11', 'اسفند': '12'
    }
    
    for month_name, month_num in persian_months.items():
        if month_name in date_str:
            date_str = date_str.replace(month_name, f'/{month_num}/')
            break
    
    # تبدیل اعداد فارسی به انگلیسی
    persian_nums = '۰۱۲۳۴۵۶۷۸۹'
    english_nums = '0123456789'
    trans_table = str.maketrans(persian_nums, english_nums)
    date_str = date_str.translate(trans_table)
    
    # سعی در یافتن فرمت YYYY/MM/DD
    date_match = re.search(r'(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})', date_str)
    if date_match:
        year = date_match.group(1)
        month = date_match.group(2).zfill(2)
        day = date_match.group(3).zfill(2)
        return f"{year}/{month}/{day}"
    
    # اگر فرمت اسلش ندارد، سعی در استخراج سه عدد
    # فرمت: "۲۶ مهر ۱۴۰۴" یا "جمعه ۲۶ مهر ۱۴۰۴"
    numbers = re.findall(r'\d+', date_str)
    
    # حذف اعداد ساعت (بیشتر از 2 رقم نیستند و بعد از ":" می‌آیند)
    # اگر عدد بعد از : باشد، حذفش کن
    filtered_numbers = []
    for i, num in enumerate(numbers):
        # چک کن آیا این عدد قبل یا بعد از : است
        num_pos = date_str.find(num)
        if num_pos > 0 and date_str[num_pos-1] == ':':
            continue  # این عدد بخشی از ساعت است
        if num_pos + len(num) < len(date_str) and date_str[num_pos + len(num)] == ':':
            continue  # این عدد قبل از : است (ساعت)
        filtered_numbers.append(num)
    
    if len(filtered_numbers) >= 3:
        # فرض: اولی روز، دومی ماه (یا نام ماه بود که نادیده گرفتیم)، سومی سال
        # اگر عدد اول > 31 باشد، احتمالاً سال است
        if int(filtered_numbers[0]) > 31:
            # فرمت: سال ماه روز (نامتعارف)
            year = filtered_numbers[0]
            month = filtered_numbers[1].zfill(2)
            day = filtered_numbers[2].zfill(2)
        else:
            # فرمت متداول: روز ماه سال
            day = filtered_numbers[0].zfill(2)
            # ماه می‌تواند عدد یا نام باشد
            if int(filtered_numbers[1]) <= 12:
                month = filtered_numbers[1].zfill(2)
            else:
                # احتمالاً سال اشتباه گرفته شده
                month = filtered_numbers[1].zfill(2)
            year = filtered_numbers[2]
        
        return f"{year}/{month}/{day}"
    
    # اگر هیچ کدام کار نکرد، فقط اعداد و / را نگه دار
    date_str = re.sub(r'[^\d/]', '', date_str)
    date_str = re.sub(r'/+', '/', date_str).strip('/')
    return date_str.strip() if date_str else None


def manual_persian_to_gregorian(persian_year, persian_month, persian_day):
    """تبدیل دستی تاریخ شمسی به میلادی (تقریبی)"""
    from datetime import date, timedelta
    
    # تاریخ مرجع: 1 فروردین 1404 = 21 مارس 2025
    base_persian = (1404, 1, 1)
    base_gregorian = date(2025, 3, 21)
    
    # محاسبه تعداد روزهای گذشته از 1 فروردین 1404
    days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]  # سال عادی
    
    days_diff = 0
    
    # اگر سال متفاوت است
    if persian_year != base_persian[0]:
        year_diff = persian_year - base_persian[0]
        days_diff += year_diff * 365  # تقریبی
    
    # اضافه کردن روزهای ماه‌های گذشته
    for m in range(1, persian_month):
        days_diff += days_in_month[m - 1]
    
    # اضافه کردن روزهای ماه جاری
    days_diff += persian_day - 1
    
    # محاسبه تاریخ میلادی
    gregorian_date = base_gregorian + timedelta(days=days_diff)
    return gregorian_date


def persian_to_gregorian_date(persian_date_str):
    """تبدیل تاریخ شمسی به میلادی"""
    if not persian_date_str:
        return None
    
    try:
        # پاک‌سازی رشته تاریخ
        date_str = clean_persian_date_string(persian_date_str)
        
        if not date_str:
            return None
        
        # تبدیل به تاریخ میلادی
        parts = date_str.split('/')
        if len(parts) == 3:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            
            if JDATETIME_AVAILABLE and jdatetime:
                # استفاده از jdatetime (دقیق)
                j_date = jdatetime.date(year, month, day)
                return j_date.togregorian()
            else:
                # استفاده از تبدیل دستی (تقریبی)
                return manual_persian_to_gregorian(year, month, day)
    except Exception as e:
        pass  # در صورت خطا، None برمی‌گرداند
    
    return None


def persian_to_gregorian_datetime(persian_datetime_str):
    """تبدیل تاریخ و ساعت شمسی به میلادی"""
    if not persian_datetime_str:
        return None
    
    try:
        # پاک‌سازی ابتدایی
        datetime_str = str(persian_datetime_str).strip()
        
        # حذف نام روز‌ها
        persian_days = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه']
        for day in persian_days:
            datetime_str = datetime_str.replace(day, '')
        
        # حذف ب.ظ و ق.ظ (ولی ساعت را نگه دار)
        has_pm = 'ب.ظ' in datetime_str or 'ب ظ' in datetime_str
        datetime_str = datetime_str.replace('ب.ظ', '').replace('ق.ظ', '').replace('ب ظ', '').replace('ق ظ', '')
        
        # تبدیل اعداد فارسی به انگلیسی
        persian_nums = '۰۱۲۳۴۵۶۷۸۹'
        english_nums = '0123456789'
        trans_table = str.maketrans(persian_nums, english_nums)
        datetime_str = datetime_str.translate(trans_table).strip()
        
        # استخراج تاریخ و ساعت با regex
        # فرمت: 1404/7/26  21:34 یا 1404/07/26 21:34
        date_match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', datetime_str)
        time_match = re.search(r'(\d{1,2}):(\d{2})', datetime_str)
        
        if date_match:
            year = int(date_match.group(1))
            month = int(date_match.group(2))
            day = int(date_match.group(3))
            
            # پردازش ساعت
            hour, minute = 0, 0
            if time_match:
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                
                # تبدیل به 24 ساعته اگر ب.ظ بود
                if has_pm and hour < 12:
                    hour += 12
            
            # تبدیل به datetime میلادی
            from datetime import datetime, timedelta
            
            if JDATETIME_AVAILABLE and jdatetime:
                j_datetime = jdatetime.datetime(year, month, day, hour, minute)
                return timezone.make_aware(j_datetime.togregorian())
            else:
                # استفاده از تبدیل دستی
                g_date = manual_persian_to_gregorian(year, month, day)
                g_datetime = datetime.combine(g_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute)
                return timezone.make_aware(g_datetime)
    except Exception as e:
        pass  # در صورت خطا، None برمی‌گرداند
    
    return None


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        exclude = [
            'teacher', 'students', 'enrolled_count', 'slug', 'created_at', 'updated_at', 'status'
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
                    persian_date = j_date.strftime('%Y/%m/%d')
                    self.fields['start_date'].initial = persian_date
                    # اگر داده‌ای در POST نیست، از initial استفاده کن
                    if not args and not kwargs.get('data'):
                        self.initial['start_date'] = persian_date
                except:
                    pass
            
            if self.instance.end_date:
                try:
                    j_date = jdatetime.date.fromgregorian(date=self.instance.end_date)
                    persian_date = j_date.strftime('%Y/%m/%d')
                    self.fields['end_date'].initial = persian_date
                    # اگر داده‌ای در POST نیست، از initial استفاده کن
                    if not args and not kwargs.get('data'):
                        self.initial['end_date'] = persian_date
                except:
                    pass
    
    def clean_start_date(self):
        """تبدیل تاریخ شمسی به میلادی"""
        from datetime import date as date_type
        
        start_date_str = self.cleaned_data.get('start_date')
        
        # اگر تاریخ date object است، همان را برگردان (تغییری نکرده)
        if isinstance(start_date_str, date_type):
            return start_date_str
        
        # اگر در حال ویرایش است و تاریخ تغییر نکرده، از مقدار فعلی استفاده کن
        if self.instance and self.instance.pk and self.instance.start_date:
            if isinstance(start_date_str, str):
                # بررسی کن آیا تاریخ تغییر کرده یا نه
                try:
                    if JDATETIME_AVAILABLE and jdatetime:
                        j_date = jdatetime.date.fromgregorian(date=self.instance.start_date)
                        current_persian = j_date.strftime('%Y/%m/%d')
                    else:
                        # تبدیل معکوس دستی
                        g_date = self.instance.start_date
                        # تاریخ مرجع
                        base_gregorian = date_type(2025, 3, 21)
                        base_persian = (1404, 1, 1)
                        
                        days_diff = (g_date - base_gregorian).days
                        # محاسبه ساده
                        persian_year = 1404 + (days_diff // 365)
                        remaining_days = days_diff % 365
                        
                        days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]
                        persian_month = 1
                        for month_days in days_in_month:
                            if remaining_days < month_days:
                                break
                            remaining_days -= month_days
                            persian_month += 1
                        
                        persian_day = remaining_days + 1
                        current_persian = f"{persian_year}/{persian_month:02d}/{persian_day:02d}"
                    
                    # اگر تاریخ تغییر نکرده، از مقدار فعلی استفاده کن
                    cleaned_input = clean_persian_date_string(start_date_str)
                    if cleaned_input == current_persian or start_date_str == current_persian:
                        return self.instance.start_date
                except Exception as e:
                    pass  # در صورت خطا، ادامه به تبدیل
        
        # اگر string است، تبدیل کن
        if isinstance(start_date_str, str):
            gregorian_date = persian_to_gregorian_date(start_date_str)
            if gregorian_date:
                return gregorian_date
            else:
                raise ValidationError('فرمت تاریخ صحیح نیست. از فرمت YYYY/MM/DD استفاده کنید (مثال: ۱۴۰۴/۰۷/۲۶)')
        
        return start_date_str
    
    def clean_end_date(self):
        """تبدیل تاریخ شمسی به میلادی"""
        from datetime import date as date_type
        
        end_date_str = self.cleaned_data.get('end_date')
        
        if not end_date_str:
            return None
        
        # اگر تاریخ date object است، همان را برگردان (تغییری نکرده)
        if isinstance(end_date_str, date_type):
            return end_date_str
        
        # اگر در حال ویرایش است و تاریخ تغییر نکرده، از مقدار فعلی استفاده کن
        if self.instance and self.instance.pk and self.instance.end_date:
            if isinstance(end_date_str, str):
                # بررسی کن آیا تاریخ تغییر کرده یا نه
                try:
                    if JDATETIME_AVAILABLE and jdatetime:
                        j_date = jdatetime.date.fromgregorian(date=self.instance.end_date)
                        current_persian = j_date.strftime('%Y/%m/%d')
                    else:
                        # تبدیل معکوس دستی
                        g_date = self.instance.end_date
                        base_gregorian = date_type(2025, 3, 21)
                        
                        days_diff = (g_date - base_gregorian).days
                        persian_year = 1404 + (days_diff // 365)
                        remaining_days = days_diff % 365
                        
                        days_in_month = [31, 31, 31, 31, 31, 31, 30, 30, 30, 30, 30, 29]
                        persian_month = 1
                        for month_days in days_in_month:
                            if remaining_days < month_days:
                                break
                            remaining_days -= month_days
                            persian_month += 1
                        
                        persian_day = remaining_days + 1
                        current_persian = f"{persian_year}/{persian_month:02d}/{persian_day:02d}"
                    
                    # اگر تاریخ تغییر نکرده، از مقدار فعلی استفاده کن
                    cleaned_input = clean_persian_date_string(end_date_str)
                    if cleaned_input == current_persian or end_date_str == current_persian:
                        return self.instance.end_date
                except Exception as e:
                    pass  # در صورت خطا، ادامه به تبدیل
        
        # اگر string است، تبدیل کن
        if isinstance(end_date_str, str):
            gregorian_date = persian_to_gregorian_date(end_date_str)
            if gregorian_date:
                return gregorian_date
            else:
                raise ValidationError('فرمت تاریخ صحیح نیست. از فرمت YYYY/MM/DD استفاده کنید (مثال: ۱۴۰۴/۰۷/۲۶)')
        
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
            'total_points', 'passing_score', 'auto_close', 'allow_late_submission'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان امتحان'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'توضیحات امتحان'}),
            'exam_type': forms.Select(attrs={'class': 'form-control'}),
            'question_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf',
                'required': True
            }),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'دستورالعمل‌های امتحان'}),
            'scheduled_start': forms.TextInput(attrs={
                'class': 'form-control persian-datetime', 
                'placeholder': 'روز/ماه/سال ساعت:دقیقه',
                'required': True
            }),
            'scheduled_end': forms.TextInput(attrs={
                'class': 'form-control persian-datetime', 
                'placeholder': 'روز/ماه/سال ساعت:دقیقه',
                'required': True
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1',
                'placeholder': 'مثال: 90',
                'required': True
            }),
            'total_points': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '1',
                'placeholder': 'مثال: 100',
                'required': True
            }),
            'passing_score': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': '0',
                'placeholder': 'مثال: 50',
                'required': True
            }),
        }
        
        labels = {
            'title': 'عنوان امتحان',
            'description': 'توضیحات',
            'exam_type': 'نوع امتحان',
            'question_file': 'فایل سوالات (PDF) *',
            'instructions': 'دستورالعمل امتحان',
            'scheduled_start': 'زمان شروع امتحان',
            'scheduled_end': 'زمان پایان امتحان',
            'duration_minutes': 'مدت امتحان (دقیقه)',
            'total_points': 'نمره کل',
            'passing_score': 'نمره قبولی',
            'auto_close': 'بسته شدن خودکار در پایان زمان',
            'allow_late_submission': 'اجازه ارسال بعد از پایان زمان',
        }
    
    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        self.course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        
        # فایل سوالات اجباری است فقط برای ایجاد
        # در ویرایش اگر فایل قبلی وجود دارد، اجباری نیست
        if not (self.instance and self.instance.pk and self.instance.question_file):
            self.fields['question_file'].required = True
        else:
            self.fields['question_file'].required = False
        
        # تبدیل تاریخ‌ها به شمسی برای ویرایش
        if JDATETIME_AVAILABLE and self.instance and self.instance.pk:
            for field_name in ['scheduled_start', 'scheduled_end']:
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
    
    def clean_question_file(self):
        """اعتبارسنجی فایل سوالات"""
        question_file = self.cleaned_data.get('question_file')
        
        # اگر در حال ویرایش است و فایل جدیدی آپلود نشده، فایل قبلی را نگه دار
        if self.instance and self.instance.pk and not question_file:
            return self.instance.question_file
        
        if not question_file:
            raise ValidationError('لطفاً فایل سوالات امتحان را آپلود کنید.')
        
        # بررسی نوع فایل
        if not question_file.name.lower().endswith('.pdf'):
            raise ValidationError('فقط فایل‌های PDF مجاز هستند.')
        
        # بررسی حجم فایل (حداکثر 20MB)
        max_size = 20 * 1024 * 1024  # 20MB
        if question_file.size > max_size:
            raise ValidationError('حجم فایل نباید بیشتر از 20 مگابایت باشد.')
        
        return question_file
    
    def clean(self):
        cleaned_data = super().clean()
        scheduled_start = cleaned_data.get('scheduled_start')
        scheduled_end = cleaned_data.get('scheduled_end')
        auto_close = cleaned_data.get('auto_close')
        allow_late_submission = cleaned_data.get('allow_late_submission')
        passing_score = cleaned_data.get('passing_score')
        total_points = cleaned_data.get('total_points')
        
        # بررسی زمان شروع و پایان
        if scheduled_start and scheduled_end:
            if scheduled_end <= scheduled_start:
                raise ValidationError('زمان پایان باید بعد از زمان شروع باشد')
        
        # بررسی نمره قبولی
        if passing_score is not None and total_points is not None:
            if passing_score > total_points:
                raise ValidationError('نمره قبولی نمی‌تواند بیشتر از نمره کل باشد')
        
        # اگر هر دو فعال باشند، خطا بده
        if auto_close and allow_late_submission:
            raise ValidationError('نمی‌توان هم‌زمان "بسته شدن خودکار" و "اجازه ارسال دیرهنگام" را فعال کرد. لطفاً یکی را انتخاب کنید.')
        
        return cleaned_data
    
    def save(self, commit=True):
        exam = super().save(commit=False)
        if self.course:
            exam.course = self.course
        if self.teacher:
            exam.teacher = self.teacher
        
        # تنظیم مقادیر پیش‌فرض برای فیلدهای حذف شده
        exam.max_attempts = 1  # فقط یک بار می‌تواند شرکت کند
        exam.randomize_questions = False  # بدون ترتیب تصادفی
        exam.show_answers_after = False  # بدون نمایش پاسخ
        exam.late_penalty_percent = 0  # بدون جریمه
        
        # امتحان در زمان شروع قابل رویت است
        exam.is_visible = True
        exam.visibility_date = exam.scheduled_start
        
        if commit:
            exam.save()
        return exam
