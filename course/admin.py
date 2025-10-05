from django.contrib import admin
from django.utils.html import format_html
from .models import Course, Category, Assignment, AssignmentSubmission

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'category', 'level', 'age_group', 'price', 'is_active', 'is_featured', 'enrolled_count', 'capacity', 'start_date', 'end_date', 'is_free', 'is_online', 'location', 'class_room_link', 'created_at', 'updated_at',)
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
        ('کلاس آنلاین', {
            'fields': ('class_room_link',),
            'classes': ('collapse',)
        }),
        ('تنظیمات', {
            'fields': ('is_active', 'is_free', 'is_featured', 'is_online')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    """Admin برای مدیریت تکالیف"""
    list_display = ('title', 'course', 'teacher', 'assignment_type', 'due_date', 'is_active', 'submission_count', 'created_at')
    list_filter = ('assignment_type', 'is_active', 'created_at', 'due_date', 'course__category')
    search_fields = ('title', 'description', 'course__title', 'teacher__user__first_name', 'teacher__user__last_name')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'submission_count')
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'description', 'assignment_type', 'course', 'teacher')
        }),
        ('فایل‌های تکلیف', {
            'fields': ('instruction_file',)
        }),
        ('زمان‌بندی', {
            'fields': ('due_date', 'late_submission_allowed', 'late_submission_penalty')
        }),
        ('امتیاز و ارزیابی', {
            'fields': ('total_points', 'passing_score', 'grading_criteria')
        }),
        ('تنظیمات', {
            'fields': ('is_active', 'allow_multiple_submissions', 'auto_grade')
        }),
        ('دستورالعمل‌های اضافی', {
            'fields': ('additional_instructions',),
            'classes': ('collapse',)
        }),
        ('آمار', {
            'fields': ('submission_count', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_assignments', 'deactivate_assignments']
    
    def submission_count(self, obj):
        """تعداد ارسال‌های تکلیف"""
        return obj.submissions.count()
    submission_count.short_description = 'تعداد ارسال‌ها'
    
    def activate_assignments(self, request, queryset):
        """فعال کردن تکالیف انتخاب شده"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} تکلیف فعال شد.')
    activate_assignments.short_description = 'فعال کردن تکالیف انتخاب شده'
    
    def deactivate_assignments(self, request, queryset):
        """غیرفعال کردن تکالیف انتخاب شده"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} تکلیف غیرفعال شد.')
    deactivate_assignments.short_description = 'غیرفعال کردن تکالیف انتخاب شده'


@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    """Admin برای مدیریت ارسال‌های تکلیف"""
    list_display = ('student_name', 'assignment_title', 'course_name', 'status', 'score_display', 'is_late', 'submitted_at', 'graded_at')
    list_filter = ('status', 'is_late', 'submitted_at', 'graded_at', 'assignment__course')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'assignment__title', 'assignment__course__title')
    date_hierarchy = 'submitted_at'
    readonly_fields = ('submitted_at', 'graded_at', 'attempt_number')
    
    fieldsets = (
        ('اطلاعات ارسال', {
            'fields': ('assignment', 'student', 'attempt_number', 'status')
        }),
        ('فایل‌های ارسالی', {
            'fields': ('submission_file', 'additional_files')
        }),
        ('محتوای متنی', {
            'fields': ('text_content', 'comments'),
            'classes': ('collapse',)
        }),
        ('نمره‌دهی', {
            'fields': ('score', 'feedback', 'graded_by', 'graded_at')
        }),
        ('وضعیت', {
            'fields': ('is_late', 'submitted_at')
        }),
    )
    
    actions = ['grade_submissions', 'mark_as_late']
    
    def student_name(self, obj):
        """نام دانش‌آموز"""
        return obj.student.user.get_full_name()
    student_name.short_description = 'دانش‌آموز'
    
    def assignment_title(self, obj):
        """عنوان تکلیف"""
        return obj.assignment.title
    assignment_title.short_description = 'تکلیف'
    
    def course_name(self, obj):
        """نام دوره"""
        return obj.assignment.course.title
    course_name.short_description = 'دوره'
    
    def score_display(self, obj):
        """نمایش نمره با رنگ‌بندی"""
        if obj.score is None:
            return format_html('<span style="color: #6c757d;">بدون نمره</span>')
        
        percentage = (obj.score / obj.assignment.total_points) * 100
        if percentage >= 70:
            color = '#28a745'  # سبز
        elif percentage >= 50:
            color = '#ffc107'  # زرد
        else:
            color = '#dc3545'  # قرمز
        
        return format_html(
            '<span style="color: {};">{}/{} ({})</span>',
            color, obj.score, obj.assignment.total_points, obj.grade_letter
        )
    score_display.short_description = 'نمره'
    
    def grade_submissions(self, request, queryset):
        """نمره‌دهی ارسال‌های انتخاب شده"""
        count = 0
        for submission in queryset.filter(status='submitted'):
            # اینجا می‌توانید منطق نمره‌دهی خودکار را اضافه کنید
            count += 1
        self.message_user(request, f'{count} ارسال برای نمره‌دهی آماده شد.')
    grade_submissions.short_description = 'نمره‌دهی ارسال‌های انتخاب شده'
    
    def mark_as_late(self, request, queryset):
        """علامت‌گذاری ارسال‌ها به عنوان دیر هنگام"""
        updated = queryset.update(is_late=True, status='late')
        self.message_user(request, f'{updated} ارسال به عنوان دیر هنگام علامت‌گذاری شد.')
    mark_as_late.short_description = 'علامت‌گذاری به عنوان دیر هنگام'
