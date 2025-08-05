from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ContactUs, AboutUs, ContactMessage


@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    """مدیریت اطلاعات تماس"""
    
    def has_add_permission(self, request):
        # فقط اگر هیچ رکوردی وجود نداشته باشد
        return not ContactUs.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # اجازه حذف داده نمی‌شود
        return False
    
    fieldsets = (
        ('📞 اطلاعات تماس اصلی', {
            'fields': ('phone', 'mobile', 'email'),
            'description': 'شماره تلفن‌ها و ایمیل رسمی آکادمی'
        }),
        ('📍 آدرس و موقعیت', {
            'fields': ('address', 'postal_code', 'map_embed_code'),
            'description': 'آدرس کامل آکادمی و کد نقشه گوگل'
        }),
        ('📱 شبکه‌های اجتماعی', {
            'fields': ('instagram', 'telegram', 'whatsapp', 'linkedin', 'youtube'),
            'description': 'لینک‌های شبکه‌های اجتماعی آکادمی'
        }),
        ('🕐 ساعات کاری', {
            'fields': ('working_hours',),
        }),
    )
    
    readonly_fields = ['updated_at']
    
    def save_model(self, request, obj, form, change):
        if not change:  # اگر رکورد جدید است
            obj.save()
        else:
            super().save_model(request, obj, form, change)


@admin.register(AboutUs)
class AboutUsAdmin(admin.ModelAdmin):
    """مدیریت صفحه درباره ما"""
    
    def has_add_permission(self, request):
        # فقط اگر هیچ رکوردی وجود نداشته باشد
        return not AboutUs.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # اجازه حذف داده نمی‌شود
        return False
    
    fieldsets = (
        ('📝 محتوای اصلی', {
            'fields': ('title', 'subtitle', 'main_content'),
            'description': 'عنوان و محتوای اصلی صفحه درباره ما'
        }),
        ('🎯 ماموریت و چشم‌انداز', {
            'fields': ('mission', 'vision', 'values'),
            'description': 'اهداف و ارزش‌های آکادمی',
            'classes': ('collapse',)  # قابل جمع شدن
        }),
        ('🖼️ تصاویر', {
            'fields': ('main_image', 'team_image'),
            'description': 'تصاویر صفحه درباره ما'
        }),
        ('📊 آمار و ارقام', {
            'fields': ('students_count', 'teachers_count', 'courses_count', 'experience_years'),
            'description': 'آمار و دستاورد های آکادمی'
        }),
        ('🔍 SEO', {
            'fields': ('meta_description',),
            'description': 'تنظیمات موتور جستجو',
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['updated_at']
    
    class Media:
        css = {
            'all': ('admin/css/admin_custom.css',)
        }


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """مدیریت پیام‌های تماس"""
    
    list_display = [
        'name', 'email', 'subject', 'status_display', 
        'created_at_display', 'action_buttons'
    ]
    
    list_filter = [
        'is_read', 'is_replied', 'created_at'
    ]
    
    search_fields = [
        'name', 'email', 'phone', 'subject', 'message'
    ]
    
    readonly_fields = [
        'name', 'email', 'phone', 'subject', 'message', 
        'created_at', 'replied_at'
    ]
    
    fieldsets = (
        ('👤 اطلاعات فرستنده', {
            'fields': ('name', 'email', 'phone', 'created_at')
        }),
        ('📧 محتوای پیام', {
            'fields': ('subject', 'message')
        }),
        ('⚙️ مدیریت', {
            'fields': ('is_read', 'is_replied', 'replied_at', 'admin_notes')
        }),
    )
    
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    actions = ['mark_as_read', 'mark_as_replied']
    
    def has_add_permission(self, request):
        return False  # پیام‌ها فقط از سایت ارسال می‌شوند
    
    def has_change_permission(self, request, obj=None):
        return True  # فقط برای علامت‌گذاری
    
    def status_display(self, obj):
        """نمایش وضعیت پیام با آیکون"""
        if obj.is_replied:
            return format_html(
                '<span style="color: green;">✅ پاسخ داده شده</span>'
            )
        elif obj.is_read:
            return format_html(
                '<span style="color: orange;">👁️ خوانده شده</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">🔴 جدید</span>'
            )
    status_display.short_description = 'وضعیت'
    
    def created_at_display(self, obj):
        """نمایش تاریخ به شکل خوانا"""
        return obj.created_at.strftime('%Y/%m/%d - %H:%M')
    created_at_display.short_description = 'تاریخ ارسال'
    
    def action_buttons(self, obj):
        """دکمه‌های عملیات"""
        buttons = []
        
        if not obj.is_read:
            buttons.append(
                f'<a href="#" onclick="markAsRead({obj.pk})" '
                f'style="background: #28a745; color: white; padding: 2px 8px; '
                f'text-decoration: none; border-radius: 3px; margin: 2px;">خوانده شد</a>'
            )
        
        if not obj.is_replied:
            buttons.append(
                f'<a href="mailto:{obj.email}?subject=پاسخ: {obj.subject}" '
                f'style="background: #007bff; color: white; padding: 2px 8px; '
                f'text-decoration: none; border-radius: 3px; margin: 2px;">پاسخ</a>'
            )
        
        return format_html(' '.join(buttons))
    action_buttons.short_description = 'عملیات'
    
    def mark_as_read(self, request, queryset):
        """علامت‌گذاری به عنوان خوانده شده"""
        updated = queryset.update(is_read=True)
        self.message_user(
            request, 
            f'{updated} پیام به عنوان خوانده شده علامت‌گذاری شد.'
        )
    mark_as_read.short_description = 'علامت‌گذاری به عنوان خوانده شده'
    
    def mark_as_replied(self, request, queryset):
        """علامت‌گذاری به عنوان پاسخ داده شده"""
        from django.utils import timezone
        updated = queryset.update(is_replied=True, replied_at=timezone.now())
        self.message_user(
            request, 
            f'{updated} پیام به عنوان پاسخ داده شده علامت‌گذاری شد.'
        )
    mark_as_replied.short_description = 'علامت‌گذاری به عنوان پاسخ داده شده'
    
    class Media:
        js = ('admin/js/contact_admin.js',)