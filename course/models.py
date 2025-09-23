from django.db import models
from teacher.models import Teacher
from account.models import Student
from datetime import date
from django.utils.text import slugify

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

    LEVEL_CHOICES = [
    ('beginner', 'مبتدی'),
    ('intermediate', 'متوسط'),
    ('advanced', 'پیشرفته'),
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
    total_hours = models.PositiveIntegerField("تعداد جلسات", default=10)  #type: ignore

    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, null=True, blank=True)
    age_group = models.CharField(max_length=20, choices=AGE_GROUP_CHOICES, null=True, blank=True)
    class_type = models.CharField("نوع کلاس", max_length=20, choices=CLASS_TYPE_CHOICES, default='general')
    exam_type = models.CharField("نوع آزمون خاص", max_length=20, blank=True, null=True)

    capacity = models.PositiveIntegerField("ظرفیت", default=20) #type: ignore
    enrolled_count = models.PositiveIntegerField("تعداد ثبت‌نام شده", default=0, editable=False)  #type: ignore
    price = models.DecimalField("شهریه", max_digits=10, decimal_places=0, default=0)
    location = models.CharField("محل برگزاری", max_length=150, null=True, blank=True)

    is_active = models.BooleanField("فعال است؟", default=True) #type: ignore
    is_free = models.BooleanField("رایگان است؟", default=False) #type: ignore
    is_featured = models.BooleanField("ویژه است؟", default=False) #type: ignore
    is_online = models.BooleanField("آنلاین است؟", default=False) #type: ignore

    image = models.ImageField("تصویر کلاس", upload_to='courses/', null=True, blank=True)
    created_at = models.DateTimeField("تاریخ ایجاد", auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField("تاریخ بروزرسانی", auto_now=True, null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.teacher})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = generate_slug(self.title or str(self.id or "course"))
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