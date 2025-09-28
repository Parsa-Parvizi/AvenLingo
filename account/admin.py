from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import User, Student, Teacher

# Remove Groups from admin panel
admin.site.unregister(Group)


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



