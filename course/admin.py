from django.contrib import admin
from .models import Course, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'category', 'level', 'age_group', 'price', 'is_active', 'is_featured', 'enrolled_count', 'capacity', 'start_date', 'end_date', 'is_free', 'is_online', 'location', 'created_at', 'updated_at',)
    list_filter = ('is_active', 'is_featured', 'is_free', 'is_online', 'level', 'age_group', 'category', 'teacher', 'start_date', 'end_date', 'created_at', 'updated_at',)
    # list_editable = ('status',)
    search_fields = ('title', 'description', 'teacher__full_name', 'location')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('enrolled_count', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'slug', 'description', 'short_description', 'image')
        }),
        ('استاد و دسته‌بندی', {
            'fields': ('teacher', 'category')
        }),
        ('زمان‌بندی', {
            'fields': ('start_date', 'end_date', 'duration', 'total_hours')
        }),
        ('سطح و گروه سنی', {
            'fields': ('level', 'age_group')
        }),
        ('ظرفیت و قیمت', {
            'fields': ('capacity', 'enrolled_count', 'price', 'location')
        }),
        ('تنظیمات', {
            'fields': ('is_active', 'is_free', 'is_featured', 'is_online')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
