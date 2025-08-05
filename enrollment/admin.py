from django.contrib import admin
from .models import Enrollment
@admin.register(Enrollment)


class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at', 'is_confirmed')
    search_fields = ('student__user__username', 'course__title')
    list_filter = ('is_confirmed', 'enrolled_at', 'course')
    ordering = ('-enrolled_at',)
