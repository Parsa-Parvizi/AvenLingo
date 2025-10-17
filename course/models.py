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
    ('hybrid', 'ترکیبی (آنلاین و آفلاین)'),
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
    ('workshop', 'کارگاه (Workshop)'),
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


class ClassType(models.Model):
    """مدل برای انواع کلاس (مکالمه، گرامر، آیلتس و غیره)"""
    
    name = models.CharField("نام نوع کلاس", max_length=100, unique=True)
    slug = models.SlugField("اسلاگ", max_length=100, unique=True, blank=True)
    code = models.CharField("کد", max_length=20, unique=True, help_text="کد منحصر به فرد (مثل: speaking, grammar, ielts)")
    description = models.TextField("توضیحات", blank=True)
    icon = models.CharField("آیکون", max_length=50, blank=True, help_text="کلاس Font Awesome یا ایموجی")
    color = models.CharField("رنگ", max_length=7, default="#667eea", help_text="کد رنگ hex")
    is_active = models.BooleanField("فعال است؟", default=True)
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)

    class Meta:
        verbose_name = "نوع کلاس"
        verbose_name_plural = "انواع کلاس"
        ordering = ['order', 'name']

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
    # تغییر به ManyToMany برای پشتیبانی از چندین دسته‌بندی
    categories = models.ManyToManyField(Category, blank=True, related_name='courses', verbose_name="دسته‌بندی‌ها")
    # نگه‌داشتن category قدیمی برای سازگاری با backward
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_old', verbose_name="دسته‌بندی اصلی")
    students = models.ManyToManyField(Student, related_name='enrolled_courses')
    
    # پیش‌نیازهای دوره
    prerequisites = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='next_courses', verbose_name="دوره‌های پیش‌نیاز")

    start_date = models.DateField("تاریخ شروع", default=date.today)
    end_date = models.DateField("تاریخ پایان", null=True, blank=True)
    duration = models.CharField("روز و ساعت برگزاری", max_length=50, null=True, blank=True, help_text="مثال: شنبه-سه‌شنبه 18:00-19:30")
    schedule_days = models.CharField("روزهای برگزاری", max_length=100, null=True, blank=True, help_text="مثال: شنبه-سه‌شنبه یا جمعه‌ها")
    schedule_time = models.CharField("ساعت برگزاری", max_length=50, null=True, blank=True, help_text="مثال: 18:00-19:30")
    class_time = models.CharField("طول کلاس", max_length=50, null=True, blank=True, default=0)
    total_hours = models.PositiveIntegerField("تعداد جلسات", default=10)  #type: ignore

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, null=True, blank=True)
    age_group = models.CharField(max_length=20, choices=AGE_GROUP_CHOICES, null=True, blank=True)
    # تغییر به ManyToMany برای پشتیبانی از چندین نوع کلاس
    class_types = models.ManyToManyField(ClassType, blank=True, related_name='courses', verbose_name="انواع کلاس")
    # نگه‌داشتن class_type قدیمی برای سازگاری
    class_type = models.CharField("نوع کلاس (قدیمی)", max_length=20, choices=CLASS_TYPE_CHOICES, default='general', blank=True, null=True)
    exam_type = models.CharField("نوع آزمون خاص", max_length=20, blank=True, null=True)

    capacity = models.PositiveIntegerField("ظرفیت", default=20) #type: ignore
    enrolled_count = models.PositiveIntegerField("تعداد ثبت‌نام شده", default=0, editable=False)  #type: ignore
    price = models.IntegerField("شهریه", default=0)

    is_active = models.BooleanField("فعال است؟", default=True) #type: ignore
    is_free = models.BooleanField("رایگان است؟", default=False) #type: ignore
    is_featured = models.BooleanField("ویژه است؟", default=False) #type: ignore
    course_type = models.CharField("نوع برگزاری", max_length=20, choices=ONLINE_CHOICES, default='online', help_text="نوع برگزاری دوره")
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
    
    @property
    def is_online(self):
        """برای سازگاری با کدهای قدیمی"""
        return self.course_type in ['online', 'hybrid']
    
    @property
    def is_offline(self):
        """آیا دوره آفلاین است"""
        return self.course_type in ['offline', 'hybrid']
    
    @property
    def is_hybrid(self):
        """آیا دوره ترکیبی است"""
        return self.course_type == 'hybrid'
    
    @property
    def is_workshop(self):
        """آیا این دوره یک کارگاه است"""
        return self.class_type == 'workshop'
    
    def is_class_time_active(self):
        """بررسی اینکه آیا الان زمان ورود به کلاس است (10 دقیقه قبل تا پایان کلاس)"""
        if not self.schedule_time or not self.schedule_days:
            # اگر زمان‌بندی مشخص نیست، همیشه فعال است
            return True
        
        from django.utils import timezone
        import re
        from datetime import datetime, timedelta
        
        now = timezone.now()
        current_weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        # نقشه روزهای فارسی به شماره
        persian_days = {
            'شنبه': 5,    # Saturday
            'یکشنبه': 6,  # Sunday  
            'دوشنبه': 0,  # Monday
            'سه‌شنبه': 1, # Tuesday
            'سه شنبه': 1,
            'سه': 1,
            'چهارشنبه': 2, # Wednesday
            'چهار‌شنبه': 2,
            'چهار': 2,
            'پنجشنبه': 3, # Thursday
            'پنج‌شنبه': 3,
            'پنج': 3,
            'جمعه': 4,    # Friday
        }
        
        # بررسی روز کلاس
        schedule_days_lower = self.schedule_days.lower()
        is_class_day = False
        
        for day_name, day_num in persian_days.items():
            if day_name in schedule_days_lower and current_weekday == day_num:
                is_class_day = True
                break
        
        if not is_class_day:
            return False
        
        # Parse زمان کلاس (مثال: "18:00-19:30" یا "۱۸:۰۰-۱۹:۳۰")
        try:
            # تبدیل اعداد فارسی به انگلیسی
            persian_nums = '۰۱۲۳۴۵۶۷۸۹'
            english_nums = '0123456789'
            trans_table = str.maketrans(persian_nums, english_nums)
            time_str = self.schedule_time.translate(trans_table)
            
            # استخراج زمان شروع و پایان
            time_pattern = r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})'
            match = re.search(time_pattern, time_str)
            
            if match:
                start_hour = int(match.group(1))
                start_minute = int(match.group(2))
                end_hour = int(match.group(3))
                end_minute = int(match.group(4))
                
                # ساخت datetime برای شروع و پایان کلاس
                class_start = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                class_end = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
                
                # 10 دقیقه قبل از کلاس
                early_access = class_start - timedelta(minutes=10)
                
                # بررسی آیا الان بین 10 دقیقه قبل و پایان کلاس است
                return early_access <= now <= class_end
            else:
                # اگر فرمت زمان صحیح نیست، همیشه فعال است
                return True
                
        except:
            # در صورت خطا، همیشه فعال است
            return True
    
    def get_class_status_message(self):
        """پیام وضعیت کلاس"""
        if not self.schedule_time or not self.schedule_days:
            return "لینک کلاس همیشه فعال است"
        
        from django.utils import timezone
        import re
        from datetime import timedelta
        
        now = timezone.now()
        current_weekday = now.weekday()
        
        persian_days = {
            'شنبه': 5, 'یکشنبه': 6, 'دوشنبه': 0, 'سه‌شنبه': 1, 'سه شنبه': 1, 'سه': 1,
            'چهارشنبه': 2, 'چهار‌شنبه': 2, 'چهار': 2, 'پنجشنبه': 3, 'پنج‌شنبه': 3, 'پنج': 3, 'جمعه': 4,
        }
        
        schedule_days_lower = self.schedule_days.lower()
        is_class_day = False
        
        for day_name, day_num in persian_days.items():
            if day_name in schedule_days_lower and current_weekday == day_num:
                is_class_day = True
                break
        
        if not is_class_day:
            return f"کلاس در روزهای {self.schedule_days} برگزار می‌شود"
        
        try:
            persian_nums = '۰۱۲۳۴۵۶۷۸۹'
            english_nums = '0123456789'
            trans_table = str.maketrans(persian_nums, english_nums)
            time_str = self.schedule_time.translate(trans_table)
            
            time_pattern = r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})'
            match = re.search(time_pattern, time_str)
            
            if match:
                start_hour = int(match.group(1))
                start_minute = int(match.group(2))
                
                class_start = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                early_access = class_start - timedelta(minutes=10)
                
                if now < early_access:
                    time_diff = early_access - now
                    minutes = int(time_diff.total_seconds() / 60)
                    if minutes < 60:
                        return f"لینک {minutes} دقیقه دیگر فعال می‌شود"
                    else:
                        hours = minutes // 60
                        return f"لینک {hours} ساعت دیگر فعال می‌شود"
                else:
                    return "کلاس در حال برگزاری است - وارد شوید"
        except:
            pass
        
        return "زمان کلاس گذشته است"
    
    def has_completed_prerequisites(self, student):
        """بررسی اینکه آیا دانشجو پیش‌نیازها را گذرانده است"""
        if not self.prerequisites.exists():
            return True
        
        from enrollment.models import Enrollment
        
        for prereq in self.prerequisites.all():
            # بررسی اینکه آیا دانشجو در دوره پیش‌نیاز ثبت‌نام کرده و آن را با موفقیت گذرانده
            enrollment = Enrollment.objects.filter(
                student=student,
                course=prereq,
                status='confirmed'
            ).first()
            
            if not enrollment:
                return False
        
        return True
    
    def get_incomplete_prerequisites(self, student):
        """دریافت لیست پیش‌نیازهای تکمیل نشده"""
        if not self.prerequisites.exists():
            return []
        
        from enrollment.models import Enrollment
        
        incomplete = []
        for prereq in self.prerequisites.all():
            enrollment = Enrollment.objects.filter(
                student=student,
                course=prereq,
                status='confirmed'
            ).first()
            
            if not enrollment:
                incomplete.append(prereq)
        
        return incomplete

    class Meta:
        verbose_name = "کلاس"
        verbose_name_plural = "کلاس‌ها"
        ordering = ['-created_at']


class CourseResource(models.Model):
    """منابع آموزشی دوره (فایل‌ها، لینک‌ها، اسناد)"""
    
    RESOURCE_TYPE_CHOICES = [
        ('pdf', 'فایل PDF'),
        ('video', 'ویدیو'),
        ('link', 'لینک'),
        ('document', 'سند'),
        ('presentation', 'ارائه'),
        ('other', 'سایر'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='resources', verbose_name="دوره")
    title = models.CharField("عنوان منبع", max_length=200)
    description = models.TextField("توضیحات", blank=True)
    resource_type = models.CharField("نوع منبع", max_length=20, choices=RESOURCE_TYPE_CHOICES, default='pdf')
    file = models.FileField("فایل", upload_to='course_resources/', blank=True, null=True)
    link = models.URLField("لینک", blank=True, null=True, help_text="لینک خارجی منبع")
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)
    is_active = models.BooleanField("فعال است؟", default=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)
    
    class Meta:
        verbose_name = "منبع آموزشی"
        verbose_name_plural = "منابع آموزشی"
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


class CourseVideo(models.Model):
    """ویدیوهای آموزشی دوره (برای دوره‌های آفلاین)"""
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='videos', verbose_name="دوره")
    title = models.CharField("عنوان ویدیو", max_length=200)
    description = models.TextField("توضیحات", blank=True)
    video_file = models.FileField("فایل ویدیو", upload_to='course_videos/', blank=True, null=True)
    video_url = models.URLField("لینک ویدیو", blank=True, null=True, help_text="لینک یوتیوب، آپارات یا سایر پلتفرم‌ها")
    duration = models.CharField("مدت زمان", max_length=20, blank=True, help_text="مثال: 45 دقیقه")
    order = models.PositiveIntegerField("ترتیب نمایش", default=0)
    is_free_preview = models.BooleanField("پیش‌نمایش رایگان", default=False, help_text="آیا این ویدیو به عنوان پیش‌نمایش رایگان نمایش داده شود؟")
    is_active = models.BooleanField("فعال است؟", default=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True)
    
    class Meta:
        verbose_name = "ویدیوی آموزشی"
        verbose_name_plural = "ویدیوهای آموزشی"
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"


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

class Exam(models.Model):
    """مدل امتحانات دوره"""
    EXAM_TYPE_CHOICES = [
        ('final', 'امتحان نهایی'),
        ('midterm', 'امتحان میان‌ترم'),
        ('quiz', 'کوییز'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'پیش‌نویس'),
        ('scheduled', 'زمان‌بندی شده'),
        ('active', 'در حال برگزاری'),
        ('ended', 'پایان یافته'),
        ('graded', 'نمره‌دهی شده'),
    ]
    
    # اطلاعات اصلی
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams', verbose_name="دوره")
    teacher = models.ForeignKey('account.Teacher', on_delete=models.CASCADE, related_name='exams', verbose_name="معلم")
    title = models.CharField(max_length=200, verbose_name="عنوان امتحان")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES, verbose_name="نوع امتحان")
    
    # فایل‌های امتحان
    question_file = models.FileField(
        upload_to='exams/questions/',
        blank=True,
        null=True,
        verbose_name="فایل سوالات",
        help_text="فایل PDF حاوی سوالات امتحان"
    )
    instructions = models.TextField(blank=True, verbose_name="دستورالعمل امتحان")
    
    # زمان‌بندی دقیق
    scheduled_start = models.DateTimeField(verbose_name="زمان شروع امتحان")
    scheduled_end = models.DateTimeField(verbose_name="زمان پایان امتحان")
    duration_minutes = models.IntegerField(verbose_name="مدت امتحان (دقیقه)")
    
    # تنظیمات رویت
    is_visible = models.BooleanField(default=False, verbose_name="قابل رویت برای دانشجو")
    visibility_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ رویت شدن",
        help_text="از چه زمانی دانشجو بتواند امتحان را ببیند"
    )
    
    # تنظیمات امتحان
    total_points = models.DecimalField(max_digits=6, decimal_places=2, default=100, verbose_name="نمره کل")
    passing_score = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="نمره قبولی")
    auto_close = models.BooleanField(default=True, verbose_name="بسته شدن خودکار")
    allow_late_submission = models.BooleanField(default=False, verbose_name="اجازه ارسال دیرهنگام")
    late_penalty_percent = models.IntegerField(default=0, verbose_name="جریمه دیرهنگام (درصد)")
    
    # تنظیمات دسترسی
    randomize_questions = models.BooleanField(default=False, verbose_name="ترتیب تصادفی سوالات")
    show_answers_after = models.BooleanField(default=False, verbose_name="نمایش پاسخ بعد از امتحان")
    max_attempts = models.IntegerField(default=1, verbose_name="حداکثر تعداد شرکت")
    
    # وضعیت
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="وضعیت")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    
    # زمان‌های سیستمی
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    
    class Meta:
        verbose_name = "امتحان"
        verbose_name_plural = "امتحانات"
        ordering = ['-scheduled_start']
        indexes = [
            models.Index(fields=['course', 'exam_type']),
            models.Index(fields=['scheduled_start']),
            models.Index(fields=['status']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(scheduled_end__gt=models.F('scheduled_start')),
                name='exam_end_after_start'
            ),
        ]
    
    def __str__(self):
        return f"{self.get_exam_type_display()} - {self.course.title}"
    
    def is_started(self):
        """آیا امتحان شروع شده است"""
        from django.utils import timezone
        return timezone.now() >= self.scheduled_start
    
    def is_ended(self):
        """آیا امتحان پایان یافته است"""
        from django.utils import timezone
        return timezone.now() >= self.scheduled_end
    
    def time_until_start(self):
        """زمان باقیمانده تا شروع"""
        from django.utils import timezone
        if self.is_started():
            return None
        return self.scheduled_start - timezone.now()
    
    def time_until_end(self):
        """زمان باقیمانده تا پایان"""
        from django.utils import timezone
        if self.is_ended():
            return None
        return self.scheduled_end - timezone.now()
    
    def can_student_see(self, student):
        """آیا دانشجو می‌تواند امتحان را ببیند"""
        from django.utils import timezone
        
        # باید فعال باشد
        if not self.is_active:
            return False, "امتحان غیرفعال است"
        
        # بررسی رویت
        if not self.is_visible:
            return False, "امتحان هنوز قابل رویت نیست"
        
        # بررسی تاریخ رویت
        if self.visibility_date and timezone.now() < self.visibility_date:
            return False, f"امتحان از {self.visibility_date} قابل رویت است"
        
        return True, "قابل رویت"
    
    def can_student_participate(self, student):
        """آیا دانشجو می‌تواند در امتحان شرکت کند"""
        from django.utils import timezone
        
        # بررسی رویت
        can_see, message = self.can_student_see(student)
        if not can_see:
            return False, message
        
        # بررسی شروع
        if not self.is_started():
            return False, "امتحان هنوز شروع نشده است"
        
        # بررسی پایان
        if self.is_ended():
            if not self.allow_late_submission:
                return False, "زمان امتحان به پایان رسیده است"
        
        # بررسی تعداد شرکت
        participation_count = ExamParticipation.objects.filter(
            exam=self,
            student=student
        ).count()
        
        if participation_count >= self.max_attempts:
            return False, f"شما قبلاً {participation_count} بار در این امتحان شرکت کرده‌اید"
        
        return True, "می‌توانید شرکت کنید"


class ExamParticipation(models.Model):
    """مدل شرکت دانشجو در امتحان"""
    STATUS_CHOICES = [
        ('started', 'شروع شده'),
        ('submitted', 'ارسال شده'),
        ('graded', 'نمره‌دهی شده'),
    ]
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='participations', verbose_name="امتحان")
    student = models.ForeignKey('account.Student', on_delete=models.CASCADE, related_name='exam_participations', verbose_name="دانشجو")
    
    # زمان‌بندی
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان شروع")
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان ارسال")
    graded_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان نمره‌دهی")
    
    # فایل‌های ارسالی
    answer_file = models.FileField(
        upload_to='exams/answers/',
        blank=True,
        null=True,
        verbose_name="فایل پاسخ"
    )
    answer_text = models.TextField(blank=True, verbose_name="پاسخ متنی")
    
    # نمره‌دهی
    score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="نمره"
    )
    feedback = models.TextField(blank=True, verbose_name="بازخورد معلم")
    graded_by = models.ForeignKey(
        'account.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_exams',
        verbose_name="نمره‌دهنده"
    )
    
    # وضعیت
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='started', verbose_name="وضعیت")
    is_late = models.BooleanField(default=False, verbose_name="دیرهنگام")
    attempt_number = models.IntegerField(default=1, verbose_name="شماره تلاش")
    
    # اطلاعات اضافی
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP آدرس")
    user_agent = models.CharField(max_length=500, blank=True, verbose_name="User Agent")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاریخ بروزرسانی")
    
    class Meta:
        verbose_name = "شرکت در امتحان"
        verbose_name_plural = "شرکت‌ها در امتحان"
        ordering = ['-started_at']
        unique_together = [['exam', 'student', 'attempt_number']]
        indexes = [
            models.Index(fields=['exam', 'student']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.exam.title}"
    
    def duration_taken(self):
        """مدت زمان شرکت در امتحان"""
        if self.submitted_at:
            delta = self.submitted_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None
    
    def save(self, *args, **kwargs):
        # بررسی دیرهنگام بودن
        if self.submitted_at and self.exam.scheduled_end:
            self.is_late = self.submitted_at > self.exam.scheduled_end
        
        # اگر دیرهنگام و جریمه فعال است
        if self.is_late and self.exam.late_penalty_percent > 0 and self.score:
            penalty = (self.score * self.exam.late_penalty_percent) / 100
            self.score = max(0, self.score - penalty)
        
        super().save(*args, **kwargs)
