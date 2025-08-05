from django.contrib import admin
from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'expertise', 'phone_number', 'is_active', 'registration_status')
    search_fields = ('user__username', 'full_name', 'expertise', 'phone_number')
    list_filter = ('is_active', 'expertise', 'registration_status')
    ordering = ('user',)
    list_editable = ('registration_status',)
