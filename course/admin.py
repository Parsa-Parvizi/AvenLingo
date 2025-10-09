from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Course, Category, Assignment, AssignmentSubmission, Exam, ExamParticipation, CourseResource, CourseVideo

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'category', 'level', 'age_group', 'price', 'is_active', 'is_featured', 'enrolled_count', 'capacity', 'start_date', 'end_date', 'is_free', 'course_type', 'class_room_link', 'created_at', 'updated_at',)
    list_filter = ('is_active', 'is_featured', 'is_free', 'course_type', 'level', 'age_group', 'category', 'teacher', 'start_date', 'end_date', 'created_at', 'updated_at',)
    # list_editable = ('status',)
    search_fields = ('title', 'description', 'teacher__full_name')
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
            'fields': ('capacity', 'enrolled_count', 'price')
        }),
        ('کلاس آنلاین', {
            'fields': ('class_room_link',),
            'classes': ('collapse',)
        }),
        ('تنظیمات', {
            'fields': ('is_active', 'is_free', 'is_featured', 'course_type')
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


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    """مدیریت امتحانات"""
    list_display = ['title_display', 'course', 'exam_type_badge', 'scheduled_start_display', 'status_badge', 'participants_count']
    list_filter = ['exam_type', 'status', 'course', 'scheduled_start']
    search_fields = ['title', 'course__title', 'description']
    ordering = ['-scheduled_start']
    readonly_fields = ['created_at', 'updated_at', 'participants_count_detail']
    
    fieldsets = (
        ('📚 اطلاعات اصلی', {
            'fields': ('course', 'teacher', 'title', 'description', 'exam_type')
        }),
        ('📄 محتوای امتحان', {
            'fields': ('question_file', 'instructions'),
        }),
        ('🕒 زمان‌بندی', {
            'fields': ('scheduled_start', 'scheduled_end', 'duration_minutes'),
            'description': 'امتحان راس ساعت شروع شروع و راس ساعت پایان بسته می‌شود'
        }),
        ('👁️ تنظیمات رویت', {
            'fields': ('is_visible', 'visibility_date'),
            'classes': ('collapse',)
        }),
        ('📊 نمره‌دهی', {
            'fields': ('total_points', 'passing_score', 'auto_close', 'allow_late_submission', 'late_penalty_percent'),
        }),
        ('⚙️ تنظیمات پیشرفته', {
            'fields': ('randomize_questions', 'show_answers_after', 'max_attempts'),
            'classes': ('collapse',)
        }),
        ('📈 وضعیت', {
            'fields': ('status', 'is_active', 'participants_count_detail'),
        }),
    )
    
    def title_display(self, obj):
        return format_html('<strong>{}</strong>', obj.title)
    title_display.short_description = 'عنوان'
    
    def exam_type_badge(self, obj):
        badges = {
            'final': '<span style="background: #F44336; color: #fff; padding: 4px 12px; border-radius: 12px;">🎓 امتحان نهایی</span>',
            'midterm': '<span style="background: #FF9800; color: #fff; padding: 4px 12px; border-radius: 12px;">📊 میان‌ترم</span>',
            'quiz': '<span style="background: #2196F3; color: #fff; padding: 4px 12px; border-radius: 12px;">❓ کوییز</span>',
        }
        return mark_safe(badges.get(obj.exam_type, obj.exam_type))
    exam_type_badge.short_description = 'نوع'
    
    def status_badge(self, obj):
        styles = {
            'draft': '<span style="background: #9E9E9E; color: #fff; padding: 4px 12px; border-radius: 12px;">📝 پیش‌نویس</span>',
            'scheduled': '<span style="background: #2196F3; color: #fff; padding: 4px 12px; border-radius: 12px;">📅 زمان‌بندی شده</span>',
            'active': '<span style="background: #4CAF50; color: #fff; padding: 4px 12px; border-radius: 12px;">▶️ در حال برگزاری</span>',
            'ended': '<span style="background: #FF9800; color: #fff; padding: 4px 12px; border-radius: 12px;">⏹️ پایان یافته</span>',
            'graded': '<span style="background: #9C27B0; color: #fff; padding: 4px 12px; border-radius: 12px;">✅ نمره‌دهی شده</span>',
        }
        return mark_safe(styles.get(obj.status, obj.status))
    status_badge.short_description = 'وضعیت'
    
    def scheduled_start_display(self, obj):
        from core.templatetags.persian_filters import jalali_datetime
        try:
            return jalali_datetime(obj.scheduled_start)
        except:
            return obj.scheduled_start.strftime('%Y/%m/%d %H:%M')
    scheduled_start_display.short_description = 'زمان شروع'
    
    def participants_count(self, obj):
        count = obj.participations.count()
        return format_html('<span style="font-weight: bold; color: #2196F3;">{} نفر</span>', count)
    participants_count.short_description = 'تعداد شرکت‌کننده'
    
    def participants_count_detail(self, obj):
        total = obj.participations.count()
        submitted = obj.participations.filter(status='submitted').count()
        graded = obj.participations.filter(status='graded').count()
        return format_html(
            'کل: {} | ارسال شده: {} | نمره‌دهی شده: {}',
            total, submitted, graded
        )
    participants_count_detail.short_description = 'جزئیات شرکت‌کنندگان'


@admin.register(ExamParticipation)
class ExamParticipationAdmin(admin.ModelAdmin):
    """مدیریت شرکت در امتحانات"""
    list_display = ['student_display', 'exam', 'started_at_display', 'status_badge', 'score_display', 'is_late']
    list_filter = ['status', 'is_late', 'exam__exam_type', 'started_at']
    search_fields = ['student__user__first_name', 'student__user__last_name', 'exam__title']
    ordering = ['-started_at']
    readonly_fields = ['started_at', 'submitted_at', 'graded_at', 'created_at', 'updated_at', 'duration_display']
    
    fieldsets = (
        ('📚 اطلاعات امتحان', {
            'fields': ('exam', 'student', 'attempt_number', 'status')
        }),
        ('📝 پاسخ‌ها', {
            'fields': ('answer_file', 'answer_text'),
        }),
        ('📊 نمره‌دهی', {
            'fields': ('score', 'feedback', 'graded_by'),
        }),
        ('🕒 زمان‌بندی', {
            'fields': ('started_at', 'submitted_at', 'graded_at', 'is_late', 'duration_display'),
            'classes': ('collapse',)
        }),
        ('🔍 اطلاعات تکمیلی', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def student_display(self, obj):
        return format_html('<strong>{}</strong>', obj.student.user.get_full_name())
    student_display.short_description = 'دانشجو'
    
    def started_at_display(self, obj):
        from core.templatetags.persian_filters import jalali_datetime
        try:
            return jalali_datetime(obj.started_at)
        except:
            return obj.started_at.strftime('%Y/%m/%d %H:%M')
    started_at_display.short_description = 'زمان شروع'
    
    def status_badge(self, obj):
        styles = {
            'started': '<span style="background: #2196F3; color: #fff; padding: 4px 12px; border-radius: 12px;">▶️ شروع شده</span>',
            'submitted': '<span style="background: #FF9800; color: #fff; padding: 4px 12px; border-radius: 12px;">✅ ارسال شده</span>',
            'graded': '<span style="background: #4CAF50; color: #fff; padding: 4px 12px; border-radius: 12px;">💯 نمره‌دهی شده</span>',
        }
        return mark_safe(styles.get(obj.status, obj.status))
    status_badge.short_description = 'وضعیت'
    
    def score_display(self, obj):
        if obj.score is not None:
            percentage = (obj.score / obj.exam.total_points * 100) if obj.exam.total_points else 0
            color = '#4CAF50' if percentage >= 60 else '#F44336'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}/{} ({}%)</span>',
                color, obj.score, obj.exam.total_points, int(percentage)
            )
        return '—'
    score_display.short_description = 'نمره'
    
    def duration_display(self, obj):
        duration = obj.duration_taken()
        if duration:
            return f'{duration} دقیقه'
        return '—'
    duration_display.short_description = 'مدت زمان'
    
    def has_add_permission(self, request):
        return False


@admin.register(CourseResource)
class CourseResourceAdmin(admin.ModelAdmin):
    """مدیریت منابع آموزشی دوره‌ها"""
    list_display = ('title', 'course', 'resource_type', 'is_active', 'order', 'created_at')
    list_filter = ('resource_type', 'is_active', 'created_at', 'course__category')
    search_fields = ('title', 'description', 'course__title')
    ordering = ['course', 'order', '-created_at']
    list_editable = ('is_active', 'order')
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('course', 'title', 'description', 'resource_type')
        }),
        ('محتوای منبع', {
            'fields': ('file', 'link')
        }),
        ('تنظیمات', {
            'fields': ('order', 'is_active')
        }),
    )


@admin.register(CourseVideo)
class CourseVideoAdmin(admin.ModelAdmin):
    """مدیریت ویدیوهای آموزشی دوره‌ها"""
    list_display = ('title', 'course', 'duration', 'is_free_preview', 'is_active', 'order', 'created_at')
    list_filter = ('is_free_preview', 'is_active', 'created_at', 'course__category')
    search_fields = ('title', 'description', 'course__title')
    ordering = ['course', 'order', '-created_at']
    list_editable = ('is_free_preview', 'is_active', 'order')
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('course', 'title', 'description', 'duration')
        }),
        ('محتوای ویدیو', {
            'fields': ('video_file', 'video_url'),
            'description': 'می‌توانید یا فایل ویدیو آپلود کنید یا لینک ویدیو را وارد کنید'
        }),
        ('تنظیمات', {
            'fields': ('order', 'is_free_preview', 'is_active')
        }),
    )
