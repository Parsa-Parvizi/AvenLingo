from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import User, Student, Teacher, TeacherApplication


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Custom admin for User model"""
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('اطلاعات شخصی', {'fields': ('first_name', 'last_name', 'user_type')}),
        ('مجوزها', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تاریخ‌های مهم', {'fields': ('last_login', 'date_joined')}),
        ('تایید ایمیل', {'fields': ('is_email_verified', 'email_verification_token')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'user_type', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Admin for Student model"""
    list_display = ('user_email', 'user_full_name', 'phone_number', 'english_level', 'enrollment_date')
    list_filter = ('english_level', 'enrollment_date', 'last_activity')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'phone_number')
    date_hierarchy = 'enrollment_date'
    
    fieldsets = (
        ('اطلاعات کاربر', {'fields': ('user',)}),
        ('اطلاعات شخصی', {'fields': ('national_id', 'phone_number', 'date_of_birth', 'address')}),
        ('اطلاعات تحصیلی', {'fields': ('english_level', 'goals')}),
        ('اطلاعات سیستم', {'fields': ('enrollment_date', 'last_activity')}),
    )
    
    readonly_fields = ('enrollment_date', 'last_activity')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'ایمیل'
    
    def user_full_name(self, obj):
        return obj.user.get_full_name()
    user_full_name.short_description = 'نام کامل'


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    """Admin for Teacher model"""
    list_display = ('user_email', 'user_full_name', 'is_active', 'is_verified', 'hourly_rate', 'joined_at')
    list_filter = ('is_active', 'is_verified', 'joined_at', 'last_activity')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'specialties')
    date_hierarchy = 'joined_at'
    
    fieldsets = (
        ('اطلاعات کاربر', {'fields': ('user', 'application')}),
        ('اطلاعات حرفه‌ای', {'fields': ('bio', 'specialties', 'hourly_rate')}),
        ('وضعیت', {'fields': ('is_active', 'is_verified')}),
        ('اطلاعات سیستم', {'fields': ('joined_at', 'last_activity')}),
    )
    
    readonly_fields = ('joined_at', 'last_activity')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'ایمیل'
    
    def user_full_name(self, obj):
        return obj.user.get_full_name()
    user_full_name.short_description = 'نام کامل'


@admin.register(TeacherApplication)
class TeacherApplicationAdmin(admin.ModelAdmin):
    """Admin for TeacherApplication model"""
    list_display = ('full_name', 'email', 'status', 'submitted_at', 'reviewed_at', 'reviewed_by')
    list_filter = ('status', 'submitted_at', 'reviewed_at')
    search_fields = ('first_name', 'last_name', 'email', 'specialties')
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('اطلاعات شخصی', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number')
        }),
        ('اطلاعات حرفه‌ای', {
            'fields': ('education', 'experience', 'certifications', 'specialties')
        }),
        ('انگیزه و رزومه', {
            'fields': ('motivation', 'cv_file')
        }),
        ('وضعیت درخواست', {
            'fields': ('status', 'admin_notes', 'reviewed_by', 'reviewed_at')
        }),
        ('اطلاعات سیستم', {
            'fields': ('submitted_at',)
        }),
    )
    
    readonly_fields = ('submitted_at', 'reviewed_at')
    
    actions = ['mark_as_accepted', 'mark_as_rejected']
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'نام کامل'
    
    def mark_as_accepted(self, request, queryset):
        """Action to mark applications as accepted"""
        updated = 0
        for application in queryset.filter(status='pending'):
            application.mark_as_accepted(request.user)
            updated += 1
        
        self.message_user(
            request,
            f'{updated} درخواست پذیرفته شد.'
        )
    mark_as_accepted.short_description = 'پذیرفتن درخواست‌های انتخاب شده'
    
    def mark_as_rejected(self, request, queryset):
        """Action to mark applications as rejected"""
        updated = 0
        for application in queryset.filter(status='pending'):
            application.mark_as_rejected(request.user, "رد شده توسط ادمین")
            updated += 1
        
        self.message_user(
            request,
            f'{updated} درخواست رد شد.'
        )
    mark_as_rejected.short_description = 'رد کردن درخواست‌های انتخاب شده'
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly based on status"""
        readonly_fields = list(self.readonly_fields)
        
        if obj and obj.status != 'pending':
            readonly_fields.extend(['status', 'admin_notes'])
        
        return readonly_fields
    
    def save_model(self, request, obj, form, change):
        """Override save to set reviewer and review date"""
        if change and 'status' in form.changed_data and obj.status != 'pending':
            if not obj.reviewed_by:
                obj.reviewed_by = request.user
            if not obj.reviewed_at:
                obj.reviewed_at = timezone.now()
        
        super().save_model(request, obj, form, change)


# Custom admin site configuration
admin.site.site_header = 'مدیریت آکادمی زبان انگلیسی'
admin.site.site_title = 'مدیریت آکادمی'
admin.site.index_title = 'پنل مدیریت'
