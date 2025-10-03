from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.admin import DateFieldListFilter

from .models import Enrollment, EnrollmentHistory


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Enrollment model"""
    
    list_display = [
        'id', 'student_name', 'course_title', 'colored_status', 
        'payment_status_badge', 'receipt_status', 'enrolled_date', 'confirmed_date', 
        'amount_info', 'actions_column'
    ]
    
    list_filter = [
        'status', 
        'payment_status', 
        'enrollment_source',
        ('enrolled_at', DateFieldListFilter),
        ('confirmed_at', DateFieldListFilter),
        'course__level',
        'course__class_type',
        'course__is_online',
    ]
    
    search_fields = [
        'student__user__first_name',
        'student__user__last_name', 
        'student__user__email',
        'course__title',
        'course__teacher__user__first_name',
        'course__teacher__user__last_name',
        'note',
        'admin_note'
    ]
    
    readonly_fields = [
        'enrolled_at', 'last_activity', 'remaining_amount', 
        'is_active', 'is_overdue_payment', 'can_be_cancelled',
        'is_course_started', 'receipt_preview'
    ]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('student', 'course', 'status', 'payment_status')
        }),
        ('اطلاعات زمانی', {
            'fields': ('enrolled_at', 'confirmed_at', 'cancelled_at', 'last_activity'),
            'classes': ('collapse',)
        }),
        ('اطلاعات مالی', {
            'fields': ('amount_paid', 'discount_applied', 'remaining_amount', 'payment_receipt', 'receipt_preview'),
            'classes': ('collapse',)
        }),
        ('جزئیات اضافی', {
            'fields': ('enrollment_source', 'completion_percentage', 'note', 'admin_note'),
            'classes': ('collapse',)
        }),
        ('وضعیت‌ها', {
            'fields': ('is_active', 'is_overdue_payment', 'can_be_cancelled', 'is_course_started'),
            'classes': ('collapse',)
        }),
    )
    
    raw_id_fields = ['student', 'course']
    
    ordering = ['-enrolled_at']
    
    date_hierarchy = 'enrolled_at'
    
    list_per_page = 25
    
    actions = ['confirm_enrollments', 'cancel_enrollments', 'mark_as_completed']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'student__user', 'course', 'course__teacher__user'
        )
    
    def student_name(self, obj):
        """Display student full name with link"""
        url = reverse('admin:account_student_change', args=[obj.student.pk])
        return format_html('<a href="{}">{}</a>', url, obj.student.user.get_full_name())
    student_name.short_description = 'دانش‌آموز'
    student_name.admin_order_field = 'student__user__first_name'
    
    def course_title(self, obj):
        """Display course title with link"""
        url = reverse('admin:course_course_change', args=[obj.course.pk])
        return format_html('<a href="{}">{}</a>', url, obj.course.title)
    course_title.short_description = 'دوره'
    course_title.admin_order_field = 'course__title'
    
    def colored_status(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': '#ffc107',
            'confirmed': '#28a745', 
            'cancelled': '#dc3545',
            'completed': '#6f42c1',
            'expired': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    colored_status.short_description = 'وضعیت'
    colored_status.admin_order_field = 'status'
    
    def payment_status_badge(self, obj):
        """Display payment status as badge"""
        badges = {
            'unpaid': 'danger',
            'paid': 'success',
            'partial': 'warning', 
            'refunded': 'info'
        }
        badge_class = badges.get(obj.payment_status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            badge_class, obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'وضعیت پرداخت'
    payment_status_badge.admin_order_field = 'payment_status'
    
    def enrolled_date(self, obj):
        """Display formatted enrollment date"""
        return obj.enrolled_at.strftime('%Y/%m/%d %H:%M') if obj.enrolled_at else '-'
    enrolled_date.short_description = 'تاریخ ثبت‌نام'
    enrolled_date.admin_order_field = 'enrolled_at'
    
    def confirmed_date(self, obj):
        """Display formatted confirmation date"""
        return obj.confirmed_at.strftime('%Y/%m/%d %H:%M') if obj.confirmed_at else '-'
    confirmed_date.short_description = 'تاریخ تأیید'
    confirmed_date.admin_order_field = 'confirmed_at'
    
    def amount_info(self, obj):
        """Display payment information"""
        total = obj.course.price - obj.discount_applied
        if obj.amount_paid >= total:
            return format_html('<span style="color: green;">✓ پرداخت کامل</span>')
        elif obj.amount_paid > 0:
            return format_html(
                '<span style="color: orange;">{:,} از {:,} تومان</span>',
                int(obj.amount_paid), int(total)
            )
        else:
            return format_html('<span style="color: red;">عدم پرداخت</span>')
    amount_info.short_description = 'وضعیت مالی'
    
    def receipt_status(self, obj):
        """Display receipt upload status"""
        if obj.payment_receipt:
            return format_html(
                '<a href="{}" target="_blank" style="color: green;">'
                '<i class="fas fa-check-circle"></i> مشاهده فیش</a>',
                obj.payment_receipt.url
            )
        else:
            return format_html('<span style="color: red;"><i class="fas fa-times-circle"></i> آپلود نشده</span>')
    receipt_status.short_description = 'فیش واریزی'
    
    def receipt_preview(self, obj):
        """Display receipt image preview in admin"""
        if obj.payment_receipt:
            return format_html(
                '<div style="margin: 10px 0;">'
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-width: 400px; max-height: 400px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />'
                '</a>'
                '<div style="margin-top: 10px;">'
                '<a href="{}" target="_blank" class="button" style="background: #10b981; color: white; padding: 8px 16px; border-radius: 5px; text-decoration: none;">'
                '<i class="fas fa-external-link-alt"></i> مشاهده در تب جدید'
                '</a>'
                '</div>'
                '</div>',
                obj.payment_receipt.url,
                obj.payment_receipt.url,
                obj.payment_receipt.url
            )
        else:
            return format_html('<p style="color: #94a3b8;">فیش واریزی آپلود نشده است.</p>')
    receipt_preview.short_description = 'پیش‌نمایش فیش'
    
    def actions_column(self, obj):
        """Display action buttons"""
        actions = []
        
        if obj.status == 'pending':
            actions.append(
                f'<a href="javascript:void(0)" onclick="confirmEnrollment({obj.id})" '
                f'class="btn btn-sm btn-success">تأیید</a>'
            )
        
        if obj.can_be_cancelled:
            actions.append(
                f'<a href="javascript:void(0)" onclick="cancelEnrollment({obj.id})" '
                f'class="btn btn-sm btn-danger">لغو</a>'
            )
            
        # History link
        history_url = reverse('admin:enrollment_enrollmenthistory_changelist')
        actions.append(
            f'<a href="{history_url}?enrollment__id__exact={obj.id}" '
            f'class="btn btn-sm btn-info">تاریخچه</a>'
        )
        
        return format_html(' '.join(actions))
    actions_column.short_description = 'عملیات'
    
    def confirm_enrollments(self, request, queryset):
        """Bulk confirm enrollments"""
        updated = 0
        for enrollment in queryset.filter(status='pending'):
            if enrollment.confirm_enrollment():
                updated += 1
                # Create history record
                EnrollmentHistory.objects.create(
                    enrollment=enrollment,
                    old_status='pending',
                    new_status='confirmed',
                    changed_by=request.user.username,
                    reason='تأیید گروهی توسط مدیر'
                )
        
        self.message_user(request, f'{updated} ثبت‌نام تأیید شد.')
    confirm_enrollments.short_description = 'تأیید ثبت‌نام‌های انتخاب شده'
    
    def cancel_enrollments(self, request, queryset):
        """Bulk cancel enrollments"""
        updated = 0
        for enrollment in queryset.filter(status__in=['pending', 'confirmed']):
            if enrollment.cancel_enrollment(reason='لغو گروهی توسط مدیر', cancelled_by=request.user.username):
                updated += 1
        
        self.message_user(request, f'{updated} ثبت‌نام لغو شد.')
    cancel_enrollments.short_description = 'لغو ثبت‌نام‌های انتخاب شده'
    
    def mark_as_completed(self, request, queryset):
        """Mark enrollments as completed"""
        updated = queryset.filter(status='confirmed').update(status='completed')
        self.message_user(request, f'{updated} ثبت‌نام به عنوان تکمیل شده علامت‌گذاری شد.')
    mark_as_completed.short_description = 'علامت‌گذاری به عنوان تکمیل شده'


@admin.register(EnrollmentHistory)
class EnrollmentHistoryAdmin(admin.ModelAdmin):
    """Admin interface for enrollment history tracking"""
    
    list_display = [
        'enrollment_info', 'status_change', 'changed_by', 
        'changed_date', 'reason_summary'
    ]
    
    list_filter = [
        'old_status', 'new_status', 
        ('changed_at', DateFieldListFilter),
        'changed_by'
    ]
    
    search_fields = [
        'enrollment__student__user__first_name',
        'enrollment__student__user__last_name',
        'enrollment__course__title',
        'changed_by',
        'reason'
    ]
    
    readonly_fields = ['enrollment', 'old_status', 'new_status', 'changed_by', 'changed_at']
    
    ordering = ['-changed_at']
    
    date_hierarchy = 'changed_at'
    
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'enrollment__student__user', 'enrollment__course'
        )
    
    def enrollment_info(self, obj):
        """Display enrollment information"""
        return f"{obj.enrollment.student.user.get_full_name()} - {obj.enrollment.course.title}"
    enrollment_info.short_description = 'ثبت‌نام'
    
    def status_change(self, obj):
        """Display status change with colors"""
        return format_html(
            '<span style="color: #dc3545;">{}</span> → <span style="color: #28a745;">{}</span>',
            obj.old_status, obj.new_status
        )
    status_change.short_description = 'تغییر وضعیت'
    
    def changed_date(self, obj):
        """Display formatted change date"""
        return obj.changed_at.strftime('%Y/%m/%d %H:%M')
    changed_date.short_description = 'تاریخ تغییر'
    changed_date.admin_order_field = 'changed_at'
    
    def reason_summary(self, obj):
        """Display truncated reason"""
        if obj.reason:
            return obj.reason[:50] + '...' if len(obj.reason) > 50 else obj.reason
        return '-'
    reason_summary.short_description = 'دلیل'


# Customize admin site header
admin.site.site_header = "مدیریت آموزشگاه زبان انگلیسی"
admin.site.site_title = "پنل مدیریت"
admin.site.index_title = "خوش آمدید به پنل مدیریت"
