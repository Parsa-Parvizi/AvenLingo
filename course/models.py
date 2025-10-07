from email.policy import default
from django.db import models
from account.models import Student, Teacher
from datetime import date, datetime
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import FileExtensionValidator

def generate_slug(value: str) -> str:
    slug = slugify(value or "", allow_unicode=True)
    return slug or "item"

LANGUAGE_CHOICES = [
    ('english', 'انگلیسی'),
    ('french', 'فرانسه'),
    ('german', 'آلمانی'),
    ('spanish', 'اسپانیایی'),
    ('arabic', 'عربی'),
    ('turkish', 'ترکی'),
    ('russian', 'روسی'),
    ('italian', 'ایتالیایی'),
    ('chinese', 'چینی'),
    ('japanese', 'ژاپنی'),
    ('persian', 'فارسی'),
    ('other', 'سایر'),
]

COURSE_TYPE_CHOICES = [
    ('general', 'عمومی'),
    ('private', 'خصوصی'),
    ('corporate', 'شرکتی'),
    ('other', 'سایر'),
]

LEVEL_CHOICES = [
    ('beginner', 'مبتدی'),
    ('intermediate', 'متوسط'),
    ('advanced', 'پیشرفته'),
]

ONLINE_CHOICES = [
    ('online', 'آنلاین'),
    ('offline', 'آفلاین'),
    ('hybrid', 'ترکیبی'),
]

AGE_GROUP_CHOICES = [
        ('kids', 'کودکان'),
        ('teens', 'نوجوانان'),
        ('adults', 'بزرگسالان'),
]

CLASS_TYPE_CHOICES = [
    ('general', 'عمومی'),
    ('grammar', 'گرامر'),
    ('writing', 'نوشتاری (Writing)'),
    ('speaking', 'مکالمه (Speaking)'),
    ('listening', 'شنیداری (Listening)'),
    ('reading', 'خواندن (Reading)'),
    ('vocabulary', 'واژگان'),
    ('conversation', 'گفت‌وگو'),
    ('exam', 'آمادگی آزمون'),
    ('ielts', 'آیلتس (IELTS)'),
    ('toefl', 'تافل (TOEFL)'),
    ('tolimo', 'تولیمو (TOLIMO)'),
    ('ept', 'ای پی تی (EPT)'),
    ('msrt', 'ام اس آر تی (MSRT)'),
    ('gre', 'جی آر ای (GRE)'),
    ('other', 'سایر'),
]

STATUS_CHOICES = [
    ('draft', 'پیش‌نویس'),
    ('published', 'منتشر شده'),
    ('archived', 'آرشیو شده'),
]


class Category(models.Model):
    name = models.CharField("نام دسته‌بندی", max_length=100)
    slug = models.SlugField("اسلاگ", max_length=100, unique=True, blank=True)
    description = models.TextField("توضیحات", blank=True)
    image = models.ImageField("تصویر", upload_to='categories/', null=True, blank=True)
    language = models.CharField("زبان", max_length=20, choices=LANGUAGE_CHOICES, default='english')
    is_active = models.BooleanField("فعال است؟", default=True) # type: ignore
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(self.name)
        super().save(*args, **kwargs)


class Course(models.Model):
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="وضعیت"
    )
    id = models.AutoField(primary_key=True)
    title = models.CharField("عنوان کلاس", max_length=150, null=True, blank=True)
    slug = models.SlugField("اسلاگ", max_length=150, unique=True, blank=True)
    description = models.TextField("توضیحات کلاس", null=True, blank=True)
    short_description = models.CharField("توضیحات کوتاه", max_length=200, blank=True)

    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name='courses')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses', verbose_name="دسته‌بندی")
    students = models.ManyToManyField(Student, related_name='enrolled_courses')

    start_date = models.DateField("تاریخ شروع", default=date.today)
    end_date = models.DateField("تاریخ پایان", null=True, blank=True)
    duration = models.CharField("ساعت برگزاری", max_length=50, null=True, blank=True)
    class_time = models.CharField("طول کلاس", max_length=50, null=True, blank=True, default=0)
    total_hours = models.PositiveIntegerField("تعداد جلسات", default=10)  #type: ignore

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, null=True, blank=True)
    age_group = models.CharField(max_length=20, choices=AGE_GROUP_CHOICES, null=True, blank=True)
    class_type = models.CharField("نوع کلاس", max_length=20, choices=CLASS_TYPE_CHOICES, default='general')
    exam_type = models.CharField("نوع آزمون خاص", max_length=20, blank=True, null=True)

    capacity = models.PositiveIntegerField("ظرفیت", default=20) #type: ignore
    enrolled_count = models.PositiveIntegerField("تعداد ثبت‌نام شده", default=0, editable=False)  #type: ignore
    price = models.IntegerField("شهریه", default=0)
    location = models.CharField("محل برگزاری", max_length=150, null=True, blank=True)

    is_active = models.BooleanField("فعال است؟", default=True) #type: ignore
    is_free = models.BooleanField("رایگان است؟", default=False) #type: ignore
    is_featured = models.BooleanField("ویژه است؟", default=False) #type: ignore
    is_online = models.BooleanField("آنلاین است؟", default=False) #type: ignore
    class_room_link = models.URLField("لینک کلاس آنلاین", blank=True, null=True, help_text="لینک Google Meet یا Zoom کلاس")

    image = models.ImageField("تصویر کلاس", upload_to='courses/', null=True, blank=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.teacher})"

    def save(self, *args, **kwargs):
        # ذخیره اولیه برای دریافت ID
        is_new = self.pk is None
        if is_new:
            super().save(*args, **kwargs)
        
        # ساخت slug با ID برای یکتا بودن
        if not self.slug or is_new:
            from core.templatetags.persian_filters import persian_numbers
            # تبدیل اعداد به فارسی در عنوان
            title_persian = persian_numbers(self.title) if self.title else f"دوره-{self.id}"
            base_slug = generate_slug(title_persian)
            self.slug = f"{base_slug}-{self.id}"
        
        if not is_new:
            super().save(*args, **kwargs)

    @property
    def available_seats(self):
        return self.capacity - self.enrolled_count  #type: ignore

    @property
    def is_full(self):
        return self.enrolled_count >= self.capacity

    class Meta:
        verbose_name = "کلاس"
        verbose_name_plural = "کلاس‌ها"
        ordering = ['-created_at']


class Assignment(models.Model):
    """مدل تکلیف برای دوره‌ها"""
    
    ASSIGNMENT_TYPE_CHOICES = [
        ('homework', 'تکلیف خانگی'),
        ('quiz', 'آزمون کوتاه'),
        ('project', 'پروژه'),
        ('exam', 'امتحان'),
        ('essay', 'مقاله'),
        ('presentation', 'ارائه'),
        ('other', 'سایر'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments', verbose_name="دوره")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='assignments', verbose_name="مدرس")
    
    title = models.CharField("عنوان تکلیف", max_length=200)
    description = models.TextField("توضیحات تکلیف", blank=True)
    assignment_type = models.CharField("نوع تکلیف", max_length=20, choices=ASSIGNMENT_TYPE_CHOICES, default='homework')
    
    # فایل‌های تکلیف
    instruction_file = models.FileField(
        "فایل دستورالعمل", 
        upload_to='assignments/instructions/', 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'rtf'])]
    )
    
    # زمان‌بندی
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    due_date = models.DateTimeField("مهلت ارسال")
    late_submission_allowed = models.BooleanField("ارسال دیر هنگام مجاز", default=False)
    late_submission_penalty = models.TextField("جریمه ارسال دیر هنگام", blank=True)
    
    # امتیاز و ارزیابی
    total_points = models.PositiveIntegerField("مجموع امتیاز", default=100)
    passing_score = models.PositiveIntegerField("نمره قبولی", default=50)
    
    # تنظیمات
    is_active = models.BooleanField("فعال", default=True)
    allow_multiple_submissions = models.BooleanField("اجازه ارسال چندگانه", default=False)
    auto_grade = models.BooleanField("نمره‌دهی خودکار", default=False)
    
    # فیلدهای اضافی
    additional_instructions = models.TextField("دستورالعمل‌های اضافی", blank=True)
    grading_criteria = models.TextField("معیارهای ارزیابی", blank=True)
    
    class Meta:
        verbose_name = "تکلیف"
        verbose_name_plural = "تکالیف"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.course.title}"
    
    @property
    def is_overdue(self):
        """بررسی آیا مهلت ارسال گذشته است"""
        return timezone.now() > self.due_date
    
    @property
    def time_remaining(self):
        """زمان باقی‌مانده تا مهلت ارسال"""
        if self.is_overdue:
            return None
        return self.due_date - timezone.now()
    
    @property
    def submission_count(self):
        """تعداد ارسال‌های تکلیف"""
        return self.submissions.count()
    
    def can_submit(self, student):
        """بررسی آیا دانش‌آموز می‌تواند تکلیف را ارسال کند"""
        # بررسی ثبت‌نام در دوره
        if not self.course.students.filter(id=student.id).exists():
            return False, "شما در این دوره ثبت‌نام نکرده‌اید"
        
        # بررسی فعال بودن تکلیف
        if not self.is_active:
            return False, "این تکلیف غیرفعال است"
        
        # بررسی مهلت ارسال
        if self.is_overdue and not self.late_submission_allowed:
            return False, "مهلت ارسال این تکلیف گذشته است"
        
        # بررسی ارسال چندگانه
        if not self.allow_multiple_submissions:
            if self.submissions.filter(student=student).exists():
                return False, "شما قبلاً این تکلیف را ارسال کرده‌اید"
        
        return True, "می‌توانید تکلیف را ارسال کنید"


class AssignmentSubmission(models.Model):
    """مدل ارسال تکلیف توسط دانش‌آموزان"""
    
    SUBMISSION_STATUS_CHOICES = [
        ('submitted', 'ارسال شده'),
        ('graded', 'نمره‌دهی شده'),
        ('returned', 'برگردانده شده'),
        ('late', 'دیر هنگام'),
        ('resubmitted', 'مجدداً ارسال شده'),
    ]
    
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions', verbose_name="تکلیف")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='assignment_submissions', verbose_name="دانش‌آموز")
    
    # فایل ارسالی
    submission_file = models.FileField(
        "فایل ارسالی", 
        upload_to='assignments/submissions/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'rtf', 'zip', 'rar'])]
    )
    additional_files = models.FileField(
        "فایل‌های اضافی", 
        upload_to='assignments/submissions/additional/',
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'rtf', 'zip', 'rar', 'jpg', 'jpeg', 'png'])]
    )
    
    # محتوای متنی (اختیاری)
    text_content = models.TextField("محتوای متنی", blank=True)
    comments = models.TextField("توضیحات دانش‌آموز", blank=True)
    
    # وضعیت و نمره
    status = models.CharField("وضعیت", max_length=20, choices=SUBMISSION_STATUS_CHOICES, default='submitted')
    score = models.PositiveIntegerField("نمره", blank=True, null=True)
    feedback = models.TextField("بازخورد مدرس", blank=True)
    
    # زمان‌بندی
    submitted_at = models.DateTimeField("تاریخ ارسال", auto_now_add=True)
    graded_at = models.DateTimeField("تاریخ نمره‌دهی", blank=True, null=True)
    graded_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_submissions', verbose_name="نمره‌دهنده")
    
    # فیلدهای اضافی
    is_late = models.BooleanField("دیر هنگام", default=False)
    attempt_number = models.PositiveIntegerField("شماره تلاش", default=1)
    
    class Meta:
        verbose_name = "ارسال تکلیف"
        verbose_name_plural = "ارسال‌های تکلیف"
        ordering = ['-submitted_at']
        unique_together = ['assignment', 'student', 'attempt_number']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.assignment.title}"
    
    def save(self, *args, **kwargs):
        # بررسی دیر هنگام بودن ارسال
        if self.submitted_at and self.assignment.due_date:
            self.is_late = self.submitted_at > self.assignment.due_date
        
        # بررسی وضعیت بر اساس نمره
        if self.score is not None and self.status == 'submitted':
            self.status = 'graded'
            if not self.graded_at:
                self.graded_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def is_passing(self):
        """بررسی آیا نمره قبولی است"""
        if self.score is None:
            return None
        return self.score >= self.assignment.passing_score
    
    @property
    def grade_letter(self):
        """تبدیل نمره به حروف"""
        if self.score is None:
            return "بدون نمره"
        
        percentage = (self.score / self.assignment.total_points) * 100
        
        if percentage >= 90:
            return "A+"
        elif percentage >= 80:
            return "A"
        elif percentage >= 70:
            return "B+"
        elif percentage >= 60:
            return "B"
        elif percentage >= 50:
            return "C+"
        elif percentage >= 40:
            return "C"
        else:
            return "F"