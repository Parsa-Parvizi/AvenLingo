from django.contrib import admin
from django.utils.html import format_html
from django.urls import get_resolver, reverse, NoReverseMatch
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from teacher.models import Teacher
from django.core.mail import send_mail
from .models import (
    FAQ, CourseGuide, CourseGuideItem, HeroSlider, Testimonial, CompanyInfo,
    FooterSection, FooterLink, SocialMedia, ContactInfo, SiteSettings, 
    AdviceRequest, DeterminationRequest, CollabrateRequest, Log, RequestCourse
)

User = get_user_model()

def get_named_url_choices():
    urlconf = get_resolver()
    choices = [("", "--- انتخاب کنید یا دستی وارد کنید ---")]
    for name, data in urlconf.reverse_dict.items():
        if not isinstance(name, str):
            continue
        if name.startswith('admin') or name == 'app_list':
            continue
        try:
            url = reverse(name)
            if url.startswith('/admin'):
                continue
            # Show name and path for clarity
            label = f"{name}  ({url})"
            choices.append((url, label))
        except Exception:
            continue
    return sorted(choices, key=lambda x: x[1])


# =============================================================================
# محتوای صفحه اصلی (Dynamic Content for Home Page)
# =============================================================================

@admin.register(HeroSlider)
class HeroSliderAdmin(admin.ModelAdmin):
    """مدیریت اسلایدرهای صفحه اصلی"""
    
    list_display = ['title', 'is_active', 'order', 'created_at', 'image_preview']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'subtitle']
    list_editable = ['is_active', 'order']
    ordering = ['order', '-created_at']
    
    fieldsets = (
        ('📝 محتوای اسلایدر', {
            'fields': ('title', 'subtitle'),
            'description': 'عنوان و متن اسلایدر'
        }),
        ('🖼️ تصویر', {
            'fields': ('image',),
            'description': 'تصویر پس‌زمینه اسلایدر'
        }),
        ('🔗 دکمه عمل', {
            'fields': ('button_text', 'button_url'),
            'description': 'دکمه‌ای که کاربران روی آن کلیک می‌کنند',
            'classes': ('collapse',)
        }),
        ('⚙️ تنظیمات', {
            'fields': ('order', 'is_active'),
            'description': 'ترتیب نمایش و وضعیت فعال/غیرفعال'
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="30" style="object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "بدون تصویر"
    image_preview.short_description = 'پیش‌نمایش'
    
    class Media:
        css = {
            'all': ('admin/css/admin_custom.css',)
        }


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """مدیریت نظرات کاربران"""
    
    list_display = ['name', 'role', 'rating_display', 'is_featured', 'is_active', 'created_at']
    list_filter = ['rating', 'is_featured', 'is_active', 'created_at']
    search_fields = ['name', 'role', 'content']
    list_editable = ['is_featured', 'is_active']
    ordering = ['-is_featured', '-created_at']
    
    fieldsets = (
        ('👤 اطلاعات شخص', {
            'fields': ('name', 'role', 'image'),
            'description': 'اطلاعات فردی که نظر داده'
        }),
        ('💬 نظر و امتیاز', {
            'fields': ('content', 'rating'),
            'description': 'متن نظر و امتیاز داده شده'
        }),
        ('⭐ تنظیمات نمایش', {
            'fields': ('is_featured', 'is_active'),
            'description': 'نظرات ویژه در صفحه اصلی نمایش داده می‌شوند'
        }),
    )
    
    def rating_display(self, obj):
        stars = '⭐' * obj.rating
        return format_html(f'{stars} ({obj.rating}/5)')
    rating_display.short_description = 'امتیاز'
    
    actions = ['mark_as_featured', 'unmark_as_featured']
    
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} نظر به عنوان ویژه انتخاب شد.')
    mark_as_featured.short_description = 'انتخاب به عنوان نظر ویژه'
    
    def unmark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} نظر از حالت ویژه خارج شد.')
    unmark_as_featured.short_description = 'حذف از نظرات ویژه'


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    """مدیریت اطلاعات کلی آکادمی"""
    
    def has_add_permission(self, request):
        return not CompanyInfo.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    fieldsets = (
        ('🏢 اطلاعات کلی', {
            'fields': ('company_name', 'slogan'),
            'description': 'نام و شعار آکادمی'
        }),
        ('🖼️ تصاویر', {
            'fields': ('logo', 'favicon'),
            'description': 'لوگو و آیکون سایت'
        }),
        ('📞 اطلاعات تماس', {
            'fields': ('main_phone', 'main_email', 'address', 'working_hours'),
            'description': 'اطلاعات تماس اصلی'
        }),
        ('📝 محتوا', {
            'fields': ('about_summary', 'copyright_text'),
            'description': 'متن‌های کوتاه برای سایت'
        }),
    )
    
    readonly_fields = ['updated_at']


# =============================================================================
# سوالات متداول و راهنمای دوره (FAQ & Course Guides)
# =============================================================================

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """مدیریت سوالات متداول"""
    
    list_display = ['question_short', 'is_active', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['question', 'answer']
    list_editable = ['is_active', 'order']
    ordering = ['order', '-created_at']
    
    fieldsets = (
        ('❓ سوال و پاسخ', {
            'fields': ('question', 'answer'),
            'description': 'سوال متداول و پاسخ کامل آن'
        }),
        ('⚙️ تنظیمات', {
            'fields': ('order', 'is_active'),
            'description': 'ترتیب نمایش (عدد کمتر = بالاتر)'
        }),
    )
    
    def question_short(self, obj):
        return obj.question[:50] + "..." if len(obj.question) > 50 else obj.question
    question_short.short_description = 'سوال'


class CourseGuideItemInline(admin.TabularInline):
    model = CourseGuideItem
    extra = 1
    fields = ['text', 'order', 'is_active']


@admin.register(CourseGuide)
class CourseGuideAdmin(admin.ModelAdmin):
    """مدیریت راهنمای دوره‌ها"""
    
    list_display = ['title', 'is_active', 'items_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['-created_at']
    inlines = [CourseGuideItemInline]
    
    def items_count(self, obj):
        count = obj.items.filter(is_active=True).count()
        return f"{count} آیتم"
    items_count.short_description = 'تعداد آیتم‌ها'


# =============================================================================
# فوتر و شبکه‌های اجتماعی (Footer & Social Media)
# =============================================================================

class FooterLinkInline(admin.TabularInline):
    model = FooterLink
    extra = 1
    fields = ['title', 'url', 'icon', 'order', 'is_active']


@admin.register(FooterSection)
class FooterSectionAdmin(admin.ModelAdmin):
    """مدیریت بخش‌های فوتر"""
    
    list_display = ['title', 'section_type', 'is_active', 'order', 'links_count']
    list_filter = ['section_type', 'is_active']
    search_fields = ['title']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'title']
    inlines = [FooterLinkInline]
    
    def links_count(self, obj):
        count = obj.links.filter(is_active=True).count()
        return f"{count} لینک"
    links_count.short_description = 'تعداد لینک‌ها'


@admin.register(SocialMedia)
class SocialMediaAdmin(admin.ModelAdmin):
    """مدیریت شبکه‌های اجتماعی"""
    
    list_display = ['platform', 'url_short', 'icon_preview', 'is_active', 'order']
    list_filter = ['platform', 'is_active']
    search_fields = ['url']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'platform']
    
    fieldsets = (
        ('📱 اطلاعات شبکه', {
            'fields': ('platform', 'url', 'is_active', 'order'),
            'description': 'انتخاب پلتفرم و آدرس صفحه'
        }),
        ('🎨 آیکون', {
            'fields': ('icon',),
            'description': 'اگر خالی باشد، آیکون پیش‌فرض انتخاب می‌شود',
            'classes': ('collapse',)
        }),
    )
    
    def url_short(self, obj):
        return obj.url[:30] + "..." if len(obj.url) > 30 else obj.url
    url_short.short_description = 'آدرس'
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html(f'<i class="{obj.icon}"></i> {obj.icon}')
        return 'آیکون پیش‌فرض'
    icon_preview.short_description = 'آیکون'


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    """مدیریت اطلاعات تماس فوتر"""
    
    list_display = ['contact_type', 'title', 'value_short', 'is_active', 'order']
    list_filter = ['contact_type', 'is_active']
    search_fields = ['title', 'value']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'contact_type']
    
    def value_short(self, obj):
        return obj.value[:30] + "..." if len(obj.value) > 30 else obj.value
    value_short.short_description = 'مقدار'


# =============================================================================
# تنظیمات کلی سایت (Site Settings - Static Boundary)
# =============================================================================

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """تنظیمات کلی سایت - غیرقابل تغییر توسط ادمین معمولی"""
    
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        # فقط سوپر ادمین
        return request.user.is_superuser
    
    list_display = ['site_name', 'updated_at']
    readonly_fields = ['updated_at']
    
    fieldsets = (
        ('⚠️ هشدار', {
            'description': '<div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 4px; color: #856404;">این تنظیمات فقط توسط مدیر فنی قابل تغییر است و تغییر آن‌ها ممکن است سایت را دچار مشکل کند.</div>',
            'fields': ()
        }),
        ('🌐 اطلاعات سایت', {
            'fields': ('site_name', 'site_description', 'logo'),
        }),
        ('📝 محتوای فوتر', {
            'fields': ('footer_description', 'copyright_text'),
        }),
        ('📧 خبرنامه', {
            'fields': ('newsletter_title', 'newsletter_description'),
        }),
    )


# =============================================================================
# درخواست‌ها و پیام‌ها (Requests & Messages - Read Only)
# =============================================================================

@admin.register(AdviceRequest)
class AdviceRequestAdmin(admin.ModelAdmin):
    """درخواست‌های مشاوره - فقط خواندنی"""
    
    list_display = ['name', 'email', 'phone', 'submitted_at']
    search_fields = ['name', 'email', 'phone']
    list_filter = ['submitted_at']
    ordering = ['-submitted_at']
    readonly_fields = ['name', 'email', 'phone', 'message', 'submitted_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DeterminationRequest)
class DeterminationRequestAdmin(admin.ModelAdmin):
    """درخواست‌های تعیین سطح - فقط خواندنی"""
    
    list_display = ['name', 'email', 'phone', 'submitted_at']
    search_fields = ['name', 'email', 'phone']
    list_filter = ['submitted_at']
    ordering = ['-submitted_at']
    readonly_fields = ['name', 'email', 'phone', 'message', 'submitted_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CollabrateRequest)
class CollabrateRequestAdmin(admin.ModelAdmin):
    """درخواست‌های همکاری"""
    
    list_display = ['name', 'email', 'phone', 'submitted_at', 'status']
    search_fields = ['name', 'email', 'phone']
    list_filter = ['submitted_at', 'status']
    ordering = ['-submitted_at']
    actions = ['approve_collabrate_requests']
    readonly_fields = ['name', 'email', 'phone', 'message', 'submitted_at']
    
    fieldsets = (
        ('👤 اطلاعات درخواست‌دهنده', {
            'fields': ('name', 'email', 'phone', 'submitted_at')
        }),
        ('💬 پیام', {
            'fields': ('message',)
        }),
        ('⚙️ مدیریت', {
            'fields': ('status',)
        }),
    )

    def approve_collabrate_requests(self, request, queryset):
        approved_group, _ = Group.objects.get_or_create(name='Teachers')
        for req in queryset:
            if req.status != 'approved':
                # ساخت User اگر وجود ندارد
                user, created = User.objects.get_or_create(username=req.email, defaults={
                    'email': req.email,
                    'first_name': req.name.split()[0] if req.name else '',
                    'last_name': ' '.join(req.name.split()[1:]) if req.name and len(req.name.split()) > 1 else '',
                    'is_active': True,
                })
                if created:
                    user.set_unusable_password()
                    user.save()
                user.groups.add(approved_group)
                # ساخت Teacher اگر وجود ندارد
                if not hasattr(user, 'teacher_profile'):
                    Teacher.objects.create(user=user, full_name=req.name, registration_status='approved')
                req.status = 'approved'
                req.save()
        self.message_user(request, 'درخواست‌های انتخاب‌شده تایید شدند و معلم جدید ساخته شد.')
    approve_collabrate_requests.short_description = 'تایید و ساخت معلم برای درخواست‌های انتخاب‌شده'

    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return True  # فقط برای تغییر وضعیت


@admin.register(RequestCourse)
class RequestCourseAdmin(admin.ModelAdmin):
    """درخواست‌های دوره - فقط خواندنی"""
    
    list_display = ['course_title', 'name', 'email', 'phone', 'created_at']
    search_fields = ['course_title', 'name', 'email', 'phone', 'description']
    list_filter = ['created_at']
    ordering = ['-created_at']
    readonly_fields = ['course_title', 'name', 'email', 'phone', 'description', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    """لاگ‌های سیستم - فقط خواندنی"""
    
    list_display = ['level', 'message_short', 'user', 'created_at']
    list_filter = ['level', 'user', 'created_at']
    search_fields = ['message', 'user__username']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['level', 'message', 'user', 'created_at']
    
    def message_short(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_short.short_description = 'پیام'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


# =============================================================================
# سفارشی‌سازی پنل ادمین
# =============================================================================

# تغییر عنوان‌های پنل ادمین
admin.site.site_header = "🎓 پنل مدیریت آکادمی زبان انگلیسی"
admin.site.site_title = "مدیریت آکادمی"
admin.site.index_title = "خوش آمدید به پنل مدیریت"