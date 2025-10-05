from django.contrib import admin
from django.utils.html import format_html
from django.urls import get_resolver, reverse, NoReverseMatch
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from account.models import Teacher
from django.core.mail import send_mail
from django.utils.safestring import mark_safe
from .models import (
    AdviceRequest, DeterminationRequest, CollabrateRequest, RequestCourse, ContactMessage
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


# Hero slider admin removed as requested


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
    
    list_display = ['name_display', 'email_display', 'phone_display', 'resume_display', 'submitted_at_display', 'status_display']
    search_fields = ['name', 'email', 'phone']
    list_filter = ['submitted_at', 'status']
    ordering = ['-submitted_at']
    actions = ['approve_collabrate_requests', 'reject_collabrate_requests']
    readonly_fields = ['name', 'email', 'phone', 'message', 'resume', 'submitted_at', 'status']
    
    fieldsets = (
        ('👤 اطلاعات درخواست‌دهنده', {
            'fields': ('name', 'email', 'phone', 'submitted_at')
        }),
        ('💬 پیام', {
            'fields': ('message',)
        }),
        ('📄 رزومه', {
            'fields': ('resume',)
        }),
        ('⚙️ وضعیت درخواست', {
            'fields': ('status',),
            'description': 'وضعیت درخواست همکاری - فقط قابل مشاهده'
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

    def reject_collabrate_requests(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} درخواست همکاری رد شد.')
    reject_collabrate_requests.short_description = 'رد کردن درخواست‌های انتخاب‌شده'

    def name_display(self, obj):
        return obj.name
    name_display.short_description = 'نام'
    
    def email_display(self, obj):
        return obj.email
    email_display.short_description = 'ایمیل'
    
    def phone_display(self, obj):
        return obj.phone
    phone_display.short_description = 'تلفن'
    
    def submitted_at_display(self, obj):
        return obj.submitted_at.strftime('%Y/%m/%d - %H:%M')
    submitted_at_display.short_description = 'تاریخ ارسال'
    
    def status_display(self, obj):
        status_choices = {
            'pending': '⏳ در انتظار بررسی',
            'approved': '✅ تایید شده',
            'rejected': '❌ رد شده'
        }
        return status_choices.get(obj.status, obj.status)
    status_display.short_description = 'وضعیت'
    
    def resume_display(self, obj):
        if obj.resume:
            return mark_safe(f'<a href="{obj.resume.url}" target="_blank">📄 مشاهده رزومه</a>')
        return '❌ رزومه ارسال نشده'
    resume_display.short_description = 'رزومه'

    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False  # فقط مشاهده، بدون امکان تغییر
    
    def has_delete_permission(self, request, obj=None):
        return False


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


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """مدیریت پیام‌های تماس با ما"""
    
    list_display = ['name_display', 'subject_display', 'email', 'status_badge', 'created_at_display']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'phone', 'subject', 'message']
    ordering = ['-created_at']
    actions = ['mark_as_read', 'mark_as_replied', 'mark_as_archived']
    list_per_page = 20
    
    fieldsets = (
        ('📧 اطلاعات فرستنده', {
            'fields': ('name', 'email', 'phone')
        }),
        ('💬 محتوای پیام', {
            'fields': ('subject', 'message')
        }),
        ('📊 وضعیت و پیگیری', {
            'fields': ('status', 'admin_note'),
            'classes': ('wide',)
        }),
        ('🕒 اطلاعات زمانی', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def name_display(self, obj):
        """نمایش نام با آیکون"""
        return format_html('<strong>👤 {}</strong>', obj.name)
    name_display.short_description = 'نام'
    
    def subject_display(self, obj):
        """نمایش موضوع با محدودیت کاراکتر"""
        if len(obj.subject) > 50:
            return format_html('<span title="{}">{} ...</span>', obj.subject, obj.subject[:50])
        return obj.subject
    subject_display.short_description = 'موضوع'
    
    def status_badge(self, obj):
        """نمایش وضعیت با badge رنگی"""
        status_styles = {
            'new': '<span style="background: #ffc107; color: #000; padding: 4px 12px; border-radius: 12px; font-weight: bold;">🆕 جدید</span>',
            'read': '<span style="background: #17a2b8; color: #fff; padding: 4px 12px; border-radius: 12px;">👁️ خوانده شده</span>',
            'replied': '<span style="background: #28a745; color: #fff; padding: 4px 12px; border-radius: 12px;">✅ پاسخ داده شده</span>',
            'archived': '<span style="background: #6c757d; color: #fff; padding: 4px 12px; border-radius: 12px;">📦 بایگانی</span>',
        }
        return mark_safe(status_styles.get(obj.status, obj.status))
    status_badge.short_description = 'وضعیت'
    
    def created_at_display(self, obj):
        """نمایش تاریخ فارسی"""
        from django.utils import timezone
        return obj.created_at.strftime('%Y/%m/%d - %H:%M')
    created_at_display.short_description = 'تاریخ ارسال'
    
    # Actions
    def mark_as_read(self, request, queryset):
        """علامت‌گذاری به عنوان خوانده شده"""
        updated = queryset.exclude(status='read').update(status='read')
        self.message_user(request, f'{updated} پیام به عنوان خوانده شده علامت‌گذاری شد.')
    mark_as_read.short_description = '👁️ علامت‌گذاری به عنوان خوانده شده'
    
    def mark_as_replied(self, request, queryset):
        """علامت‌گذاری به عنوان پاسخ داده شده"""
        updated = queryset.update(status='replied')
        self.message_user(request, f'{updated} پیام به عنوان پاسخ داده شده علامت‌گذاری شد.')
    mark_as_replied.short_description = '✅ علامت‌گذاری به عنوان پاسخ داده شده'
    
    def mark_as_archived(self, request, queryset):
        """بایگانی کردن پیام‌ها"""
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} پیام بایگانی شد.')
    mark_as_archived.short_description = '📦 بایگانی کردن'
    
    def has_add_permission(self, request):
        """غیرفعال کردن امکان افزودن دستی"""
        return False
    
    def get_readonly_fields(self, request, obj=None):
        """فیلدهای فقط خواندنی"""
        if obj:  # در حالت ویرایش
            return ['name', 'email', 'phone', 'subject', 'message', 'created_at', 'updated_at']
        return ['created_at', 'updated_at']


# @admin.register(Log)
# class LogAdmin(admin.ModelAdmin):
#     """لاگ‌های سیستم - فقط خواندنی"""
    
#     list_display = ['level', 'message_short', 'user', 'created_at']
#     list_filter = ['level', 'user', 'created_at']
#     search_fields = ['message', 'user__username']
#     ordering = ['-created_at']
#     date_hierarchy = 'created_at'
#     readonly_fields = ['level', 'message', 'user', 'created_at']
    
#     def message_short(self, obj):
#         return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
#     message_short.short_description = 'پیام'
    
#     def has_add_permission(self, request):
#         return False
    
#     def has_change_permission(self, request, obj=None):
#         return False
    
#     def has_delete_permission(self, request, obj=None):
#         return False


admin.site.site_header = "🎓 پنل مدیریت آکادمی زبان انگلیسی"
admin.site.site_title = "مدیریت آکادمی"
admin.site.index_title = "خوش آمدید به پنل مدیریت"