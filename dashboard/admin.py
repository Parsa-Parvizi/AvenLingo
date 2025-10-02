from django.contrib import admin
from .models import LoginHistory, CourseRequest, ConsultationRequest, SecuritySettings


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_time', 'logout_time', 'ip_address', 'device_type', 'is_successful']
    list_filter = ['is_successful', 'device_type', 'login_time']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['login_time', 'logout_time', 'duration']
    date_hierarchy = 'login_time'


@admin.register(CourseRequest)
class CourseRequestAdmin(admin.ModelAdmin):
    list_display = ['course_title', 'user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['course_title', 'user__email', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = ['subject', 'user', 'status', 'scheduled_date', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['subject', 'user__email', 'description']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(SecuritySettings)
class SecuritySettingsAdmin(admin.ModelAdmin):
    list_display = ['updated_at', 'updated_by', 'min_password_length', 'enable_2fa']
    readonly_fields = ['updated_at']
    
    def has_add_permission(self, request):
        # فقط یک instance مجاز است
        return not SecuritySettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # نمی‌توان تنظیمات را حذف کرد
        return False
