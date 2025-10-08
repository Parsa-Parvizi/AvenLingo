from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView, DetailView
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from account.models import Student, Teacher, User, TeacherApplication
from course.models import Course, Category, Assignment
from enrollment.models import Enrollment
from core.models import DeterminationRequest

logger = logging.getLogger('dashboard')


class DashboardView(LoginRequiredMixin, TemplateView):
    """Universal dashboard that redirects to appropriate user dashboard"""

    def get(self, request, *args, **kwargs):
        user = request.user

        # فقط superuser به admin calendar می‌رود
        if user.is_superuser:
            return redirect('dashboard:admin_calendar')
        elif user.user_type == 'student':
            return redirect('dashboard:student_calendar')
        elif user.user_type == 'teacher':
            return redirect('dashboard:teacher_dashboard')
        else:
            messages.error(request, 'نوع کاربری نامعتبر است.')
            return redirect('account:login')


class StudentDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Dashboard for students"""
    template_name = 'account/student_dashboard.html'

    def test_func(self):
        from .permissions import is_student
        return is_student(self.request.user)

    def dispatch(self, request, *args, **kwargs):
        # اگر کاربر superuser است، اجازه دسترسی به student dashboard را نده
        if request.user.is_superuser:
            messages.error(request, 'کاربران ادمین باید از داشبورد مدیریت استفاده کنند.')
            return redirect('dashboard:admin_calendar')
            
        try:
            _ = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            if request.user.user_type == 'student':
                Student.objects.create(user=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = get_object_or_404(Student, user=self.request.user)
        context['student'] = student

        from enrollment.models import Enrollment
        from course.models import Course

        # Get all enrollments for the student
        enrollments = Enrollment.objects.filter(student=student).select_related(
            'course', 'course__teacher', 'course__category'
        ).order_by('-enrolled_at')
        
        # Get confirmed enrollments for "My Courses" section (only confirmed courses)
        confirmed_enrollments_queryset = enrollments.filter(status='confirmed').select_related(
            'course', 'course__teacher', 'course__category'
        ).order_by('-enrolled_at')
        
        context['enrollments'] = enrollments
        context['confirmed_enrollments'] = confirmed_enrollments_queryset
        context['total_enrollments'] = enrollments.count()
        context['confirmed_enrollments_count'] = enrollments.filter(status='confirmed').count()
        context['pending_enrollments'] = enrollments.filter(status='pending').count()
        context['cancelled_enrollments'] = enrollments.filter(status='cancelled').count()
        context['completed_enrollments'] = enrollments.filter(status='completed').count()

        context['paid_enrollments'] = enrollments.filter(payment_status='paid').count()
        context['unpaid_enrollments'] = enrollments.filter(payment_status='unpaid').count()
        context['overdue_payments'] = enrollments.filter(
            payment_status='unpaid',
            status__in=['confirmed', 'pending']
        ).count()

        # Add stats for student dashboard
        context['stats'] = {
            'profile_completion': student.get_profile_completion_percentage(),
            'total_courses': enrollments.count(),
            'active_courses': context['confirmed_enrollments_count'],
            'pending_courses': context['pending_enrollments'],
            'completed_courses': context['completed_enrollments'],
        }

        # Get enrolled course IDs to exclude from suggestions
        enrolled_course_ids = enrollments.values_list('course_id', flat=True)
        
        # Get suggested courses (excluding already enrolled ones)
        # Prioritize recent courses and featured courses
        available_courses = Course.objects.filter(
            is_active=True,
            status='published'
        ).exclude(id__in=enrolled_course_ids).select_related(
            'teacher__user', 'category'
        ).order_by('-is_featured', '-created_at')[:6]
        
        context['available_courses'] = available_courses

        try:
            from account.models import PageContent
            dashboard_content = PageContent.objects.get(page_type='student_dashboard', is_active=True)
            context['dashboard_content'] = dashboard_content
        except Exception:
            context['dashboard_content'] = None

        # Calculate learning progress
        total_confirmed = context['confirmed_enrollments_count'] + context['completed_enrollments']
        if total_confirmed > 0:
            context['learning_progress'] = {
                'completion_rate': int((context['completed_enrollments'] / total_confirmed) * 100),
                'active_rate': int((context['confirmed_enrollments_count'] / total_confirmed) * 100),
            }
        else:
            context['learning_progress'] = {'completion_rate': 0, 'active_rate': 0}

        return context


class TeacherDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Enhanced dashboard for teachers"""
    template_name = 'account/teacher_dashboard.html'

    def test_func(self):
        from .permissions import is_teacher
        return is_teacher(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, 'دسترسی غیرمجاز به داشبورد مدرس.')
        return redirect('core:home')

    def dispatch(self, request, *args, **kwargs):
        # اگر کاربر superuser است، اجازه دسترسی به teacher dashboard را نده
        if request.user.is_superuser:
            messages.error(request, 'کاربران ادمین باید از داشبورد مدیریت استفاده کنند.')
            return redirect('dashboard:admin_calendar')
            
        try:
            _ = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
            if request.user.user_type == 'teacher':
                messages.error(request, 'حساب مدرس شما هنوز تکمیل/تایید نشده است. لطفاً پس از تایید ادمین ثبت‌نام مدرس را تکمیل کنید.')
                return redirect('core:collaborate')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = get_object_or_404(Teacher, user=self.request.user)
        context['teacher'] = teacher

        from course.models import Course, Assignment, Exam
        from enrollment.models import Enrollment
        from django.utils import timezone
        from datetime import datetime, timedelta
        from django.db.models import Count, Sum, Avg
        import json

        courses = Course.objects.filter(teacher=teacher.pk, is_active=True).select_related('category')
        context['courses'] = courses
        context['total_courses'] = courses.count()

        total_students = sum(course.enrolled_count for course in courses)
        context['total_students'] = total_students

        # تکالیف در انتظار بررسی
        from course.models import AssignmentSubmission
        pending_submissions = AssignmentSubmission.objects.filter(
            assignment__course__teacher=teacher,
            graded_by__isnull=True
        ).count()
        context['pending_assignments'] = pending_submissions

        # کلاس‌های پیش رو این هفته
        today = timezone.now().date()
        week_end = today + timedelta(days=7)
        upcoming_classes = courses.filter(
            start_date__lte=week_end,
            end_date__gte=today
        ).count()
        context['upcoming_classes'] = upcoming_classes

        recent_enrollments = Enrollment.objects.filter(
            course__teacher=teacher.pk
        ).select_related('student__user', 'course').order_by('-enrolled_at')[:5]
        context['recent_enrollments'] = recent_enrollments

        # رویدادهای تقویم
        events = []
        
        # کلاس‌ها
        for course in courses:
            if course.start_date and course.end_date:
                events.append({
                    'id': f'course-{course.id}',
                    'title': f'📚 {course.title}',
                    'start': course.start_date.isoformat(),
                    'end': course.end_date.isoformat(),
                    'color': '#4CAF50',
                    'url': f'/teachers/courses/{course.id}/students/'
                })
        
        # تکالیف
        assignments = Assignment.objects.filter(course__teacher=teacher)
        for assignment in assignments:
            events.append({
                'id': f'assignment-{assignment.id}',
                'title': f'📝 {assignment.title}',
                'start': assignment.due_date.isoformat(),
                'color': '#2196F3',
            })
        
        # امتحانات
        exams = Exam.objects.filter(course__teacher=teacher)
        for exam in exams:
            color = '#F44336' if exam.exam_type == 'final' else '#FF5722' if exam.exam_type == 'midterm' else '#9C27B0'
            events.append({
                'id': f'exam-{exam.id}',
                'title': f'📋 {exam.title}',
                'start': exam.scheduled_start.isoformat(),
                'end': exam.scheduled_end.isoformat() if exam.scheduled_end else None,
                'color': color,
            })
        
        context['events_json'] = json.dumps(events, ensure_ascii=False)

        # Enhanced course statistics
        context['course_stats'] = {
            'total_courses': courses.count(),
            'published_courses': courses.filter(is_active=True).count(),
            'draft_courses': courses.filter(is_active=False).count(),
            'total_students': total_students,
            'active_students': sum(
                course.students.filter(
                    enrollments__status='confirmed'
                ).count() for course in courses
            )
        }

        # Monthly earnings calculation
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_enrollments = Enrollment.objects.filter(
            course__teacher=teacher.pk,
            enrolled_at__gte=current_month,
            payment_status='paid'
        )
        
        monthly_earnings = {
            'total': sum(enrollment.course.price or 0 for enrollment in monthly_enrollments),
            'new_enrollments': monthly_enrollments.count(),
            'daily_average': 0
        }
        
        days_in_month = (timezone.now() - current_month).days + 1
        if days_in_month > 0:
            monthly_earnings['daily_average'] = monthly_earnings['total'] / days_in_month
            
        context['monthly_earnings'] = monthly_earnings

        # Weekly earnings for chart
        weekly_earnings = []
        for week in range(4):
            week_start = current_month + timedelta(weeks=week)
            week_end = week_start + timedelta(weeks=1)
            week_enrollments = Enrollment.objects.filter(
                course__teacher=teacher.pk,
                enrolled_at__gte=week_start,
                enrolled_at__lt=week_end,
                payment_status='paid'
            )
            weekly_total = sum(enrollment.course.price or 0 for enrollment in week_enrollments)
            weekly_earnings.append(weekly_total)
        
        context['weekly_earnings'] = ','.join(map(str, weekly_earnings))

        # Notifications (placeholder - you can implement actual notification system)
        context['notifications'] = []
        context['notifications_count'] = 0
        context['unread_messages_count'] = 0

        context['recent_activities'] = self.get_recent_activities(teacher)

        # Get recent assignments for the teacher
        recent_assignments = Assignment.objects.filter(
            teacher=teacher
        ).select_related('course').order_by('-created_at')[:5]
        context['recent_assignments'] = recent_assignments

        # Assignment statistics
        all_assignments = Assignment.objects.filter(teacher=teacher)
        context['assignment_stats'] = {
            'total_assignments': all_assignments.count(),
            'active_assignments': all_assignments.filter(is_active=True).count(),
            'homework_count': all_assignments.filter(assignment_type='homework').count(),
            'quiz_count': all_assignments.filter(assignment_type='quiz').count(),
            'project_count': all_assignments.filter(assignment_type='project').count(),
            'exam_count': all_assignments.filter(assignment_type='exam').count(),
        }

        return context

    def get_recent_activities(self, teacher):
        from enrollment.models import Enrollment
        from course.models import Course

        activities = []

        recent_courses = Course.objects.filter(
            teacher=teacher.pk
        ).order_by('-created_at')[:3]

        for course in recent_courses:
            activities.append({
                'type': 'course_created',
                'title': f'دوره "{course.title}" ایجاد شد',
                'date': course.created_at,
                'icon': 'fas fa-book',
                'color': 'primary'
            })

        recent_enrollments = Enrollment.objects.filter(
            course__teacher=teacher.pk
        ).select_related('student__user', 'course').order_by('-enrolled_at')[:3]

        for enrollment in recent_enrollments:
            activities.append({
                'type': 'student_enrolled',
                'title': f'{enrollment.student.user.get_full_name()} در دوره "{enrollment.course.title}" ثبت‌نام کرد',
                'date': enrollment.enrolled_at,
                'icon': 'fas fa-user-plus',
                'color': 'success'
            })

        activities.sort(key=lambda x: x['date'], reverse=True)
        return activities[:5]


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Dashboard اختصاصی برای Super User با تمام امکانات مدیریتی"""
    template_name = 'dashboard/admin_dashboard.html'
    
    def test_func(self):
        """فقط superuser دسترسی دارد - امنیت بالا"""
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, 'دسترسی غیرمجاز به داشبورد مدیریت.')
        return redirect('core:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # آمار کلی سیستم
        context.update({
            'total_students': Student.objects.count(),
            'active_students': Student.objects.filter(user__is_active=True).count(),
            'total_teachers': Teacher.objects.count(),
            'active_teachers': Teacher.objects.filter(user__is_active=True).count(),
            'total_courses': Course.objects.count(),
            'active_courses': Course.objects.filter(is_active=True).count(),
            'total_enrollments': Enrollment.objects.count(),
            'pending_enrollments': Enrollment.objects.filter(status='pending').count(),
            'pending_applications': TeacherApplication.objects.filter(status='pending').count(),
        })
        
        # آمار ثبت‌نام‌ها
        enrollments = Enrollment.objects.all()
        context['enrollment_stats'] = {
            'confirmed': enrollments.filter(status='confirmed').count(),
            'pending': enrollments.filter(status='pending').count(),
            'cancelled': enrollments.filter(status='cancelled').count(),
            'completed': enrollments.filter(status='completed').count(),
        }
        
        # آمار پرداخت‌ها
        context['payment_stats'] = {
            'paid': enrollments.filter(payment_status='paid').count(),
            'unpaid': enrollments.filter(payment_status='unpaid').count(),
            'partial': enrollments.filter(payment_status='partial').count(),
        }
        
        # آمار ماهانه
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_enrollments = enrollments.filter(enrolled_at__gte=current_month)
        
        context['monthly_stats'] = {
            'new_students': Student.objects.filter(enrollment_date__gte=current_month).count(),
            'new_courses': Course.objects.filter(created_at__gte=current_month).count(),
            'new_enrollments': monthly_enrollments.count(),
            'revenue': sum(e.amount_paid for e in monthly_enrollments.filter(payment_status='paid')),
        }
        
        # آخرین فعالیت‌ها
        context['recent_enrollments'] = Enrollment.objects.select_related(
            'student__user', 'course', 'course__teacher__user'
        ).order_by('-enrolled_at')[:10]
        
        context['recent_students'] = Student.objects.select_related('user').order_by('-enrollment_date')[:10]
        context['recent_applications'] = TeacherApplication.objects.filter(status='pending').order_by('-submitted_at')[:10]
        
        # نمودار ثبت‌نام‌های ماهانه (12 ماه گذشته)
        monthly_data = []
        for i in range(12):
            month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            count = Enrollment.objects.filter(
                enrolled_at__gte=month_start,
                enrolled_at__lt=month_end
            ).count()
            monthly_data.insert(0, count)
        
        context['monthly_enrollment_data'] = ','.join(map(str, monthly_data))
        
        # نمودار دوره‌های محبوب
        popular_courses = Course.objects.annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count')[:5]
        
        context['popular_courses'] = popular_courses
        
        # محبوب‌ترین معلمان (بر اساس تعداد ثبت‌نام‌های تأیید شده)
        popular_teachers = Teacher.objects.annotate(
            confirmed_enrollments=Count(
                'courses__enrollments',
                filter=Q(courses__enrollments__status='confirmed')
            )
        ).filter(confirmed_enrollments__gt=0).order_by('-confirmed_enrollments')[:5]
        
        context['popular_teachers'] = popular_teachers
        
        return context


class AdminUsersListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """لیست کاربران برای مدیریت"""
    template_name = 'dashboard/admin_users.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # فیلترها
        user_type = self.request.GET.get('user_type', 'all')
        is_active = self.request.GET.get('is_active', 'all')
        search_query = self.request.GET.get('search', '')
        
        users = User.objects.all()
        
        if user_type != 'all':
            users = users.filter(user_type=user_type)
        
        if is_active == 'active':
            users = users.filter(is_active=True)
        elif is_active == 'inactive':
            users = users.filter(is_active=False)
        
        if search_query:
            users = users.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        # Pagination
        from django.core.paginator import Paginator
        users_ordered = users.order_by('-date_joined')
        paginator = Paginator(users_ordered, 10)  # 10 کاربر در هر صفحه
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context['users'] = page_obj
        context['user_type_filter'] = user_type
        context['is_active_filter'] = is_active
        context['search_query'] = search_query
        
        # اگر فیلتر روی معلمان است، لیست محبوب‌ترین‌ها را نمایش بده
        if user_type == 'teacher':
            popular_teachers = Teacher.objects.filter(
                is_active=True
            ).select_related('user').annotate(
                confirmed_enrollments=Count('courses__enrollments',
                                          filter=Q(courses__enrollments__status='confirmed')),
                active_courses_count=Count('courses', filter=Q(courses__is_active=True))
            ).filter(confirmed_enrollments__gt=0).order_by('-confirmed_enrollments')[:10]
            
            context['popular_teachers'] = popular_teachers
        
        return context


class AdminCoursesListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """لیست دوره‌ها برای مدیریت"""
    template_name = 'dashboard/admin_courses.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # فیلترها
        status = self.request.GET.get('status', 'all')
        is_active = self.request.GET.get('is_active', 'all')
        category = self.request.GET.get('category', 'all')
        search_query = self.request.GET.get('search', '')
        
        courses = Course.objects.select_related('teacher__user', 'category').all()
        
        if status != 'all':
            courses = courses.filter(status=status)
        
        if is_active == 'active':
            courses = courses.filter(is_active=True)
        elif is_active == 'inactive':
            courses = courses.filter(is_active=False)
        
        if category != 'all':
            courses = courses.filter(category_id=category)
        
        if search_query:
            courses = courses.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Pagination
        from django.core.paginator import Paginator
        courses_ordered = courses.order_by('-created_at')
        paginator = Paginator(courses_ordered, 10)  # 10 دوره در هر صفحه
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context['courses'] = page_obj
        context['categories'] = Category.objects.all()
        context['status_filter'] = status
        context['is_active_filter'] = is_active
        context['category_filter'] = category
        context['search_query'] = search_query
        
        # لیست محبوب‌ترین دوره‌ها
        popular_courses = Course.objects.filter(
            is_active=True
        ).select_related('teacher__user', 'category').annotate(
            enrollment_count=Count('enrollments', filter=Q(enrollments__status='confirmed'))
        ).filter(enrollment_count__gt=0).order_by('-enrollment_count')[:10]
        
        context['popular_courses'] = popular_courses
        
        return context


class AdminEnrollmentsListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """لیست ثبت‌نام‌ها برای مدیریت"""
    template_name = 'dashboard/admin_enrollments.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # فیلترها
        status = self.request.GET.get('status', 'all')
        payment_status = self.request.GET.get('payment_status', 'all')
        search_query = self.request.GET.get('search', '')
        
        enrollments = Enrollment.objects.select_related(
            'student__user', 'course', 'course__teacher__user'
        ).all()
        
        if status != 'all':
            enrollments = enrollments.filter(status=status)
        
        if payment_status != 'all':
            enrollments = enrollments.filter(payment_status=payment_status)
        
        if search_query:
            enrollments = enrollments.filter(
                Q(student__user__first_name__icontains=search_query) |
                Q(student__user__last_name__icontains=search_query) |
                Q(course__title__icontains=search_query)
            )
        
        # Pagination
        from django.core.paginator import Paginator
        enrollments_ordered = enrollments.order_by('-enrolled_at')
        paginator = Paginator(enrollments_ordered, 10)  # 10 ثبت‌نام در هر صفحه
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context['enrollments'] = page_obj
        context['status_filter'] = status
        context['payment_status_filter'] = payment_status
        context['search_query'] = search_query
        
        # آمار وضعیت ثبت‌نام‌ها برای نمودار
        enrollment_stats = {
            'confirmed': Enrollment.objects.filter(status='confirmed').count(),
            'pending': Enrollment.objects.filter(status='pending').count(),
            'cancelled': Enrollment.objects.filter(status='cancelled').count(),
            'completed': Enrollment.objects.filter(status='completed').count(),
        }
        context['enrollment_stats'] = enrollment_stats
        
        # داده‌های نمودار ثبت‌نام‌های ماهانه (12 ماه گذشته)
        monthly_data = []
        for i in range(11, -1, -1):
            month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            count = Enrollment.objects.filter(
                enrolled_at__gte=month_start,
                enrolled_at__lt=month_end
            ).count()
            
            monthly_data.append(str(count))
        
        context['monthly_enrollment_data'] = ', '.join(monthly_data)
        
        return context


class AdminFinancialView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """مدیریت مالی و گزارشات مالی"""
    template_name = 'dashboard/admin_financial.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from decimal import Decimal
        
        # فیلترها
        teacher_filter = self.request.GET.get('teacher', 'all')
        course_filter = self.request.GET.get('course', 'all')
        payment_filter = self.request.GET.get('payment_status', 'all')
        from_date = self.request.GET.get('from_date', '')
        to_date = self.request.GET.get('to_date', '')
        
        # لیست معلمان و دوره‌ها برای فیلتر
        context['teachers'] = Teacher.objects.select_related('user').filter(is_active=True)
        context['courses'] = Course.objects.select_related('teacher__user').filter(is_active=True)
        
        # تراکنش‌ها (ثبت‌نام‌ها)
        transactions = Enrollment.objects.select_related(
            'student__user', 'course', 'course__teacher__user'
        ).all()
        
        # اعمال فیلترها
        if teacher_filter != 'all':
            transactions = transactions.filter(course__teacher__id=teacher_filter)
        
        if course_filter != 'all':
            transactions = transactions.filter(course__id=course_filter)
        
        if payment_filter != 'all':
            transactions = transactions.filter(payment_status=payment_filter)
        
        if from_date:
            transactions = transactions.filter(enrolled_at__gte=from_date)
        
        if to_date:
            transactions = transactions.filter(enrolled_at__lte=to_date)
        
        # Pagination
        from django.core.paginator import Paginator
        transactions_ordered = transactions.order_by('-enrolled_at')
        paginator = Paginator(transactions_ordered, 10)  # 10 تراکنش در هر صفحه
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context['transactions'] = page_obj
        context['total_transactions_count'] = transactions.count()
        context['teacher_filter'] = teacher_filter
        context['course_filter'] = course_filter
        context['payment_filter'] = payment_filter
        context['from_date'] = from_date
        context['to_date'] = to_date
        
        # محاسبات مالی کلی
        paid_enrollments = Enrollment.objects.filter(payment_status='paid')
        pending_enrollments = Enrollment.objects.filter(payment_status='unpaid')
        
        # کل درآمد
        total_revenue = paid_enrollments.aggregate(
            total=Sum('amount_paid')
        )['total'] or Decimal('0')
        
        # درآمد ماه جاری
        current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = paid_enrollments.filter(
            enrolled_at__gte=current_month_start
        ).aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
        
        # پرداخت‌های در انتظار
        pending_payments = pending_enrollments.aggregate(
            total=Sum('amount_paid')
        )['total'] or Decimal('0')
        pending_count = pending_enrollments.count()
        
        # محاسبه سهم معلمان و پلتفرم (فرض: 70% معلم، 30% پلتفرم)
        teacher_share = total_revenue * Decimal('0.7')
        platform_profit = total_revenue * Decimal('0.3')
        monthly_teacher_share = monthly_revenue * Decimal('0.7')
        monthly_platform_profit = monthly_revenue * Decimal('0.3')
        
        context['total_revenue'] = total_revenue
        context['monthly_revenue'] = monthly_revenue
        context['pending_payments'] = pending_payments
        context['pending_count'] = pending_count
        context['teacher_share'] = teacher_share
        context['platform_profit'] = platform_profit
        context['monthly_teacher_share'] = monthly_teacher_share
        context['monthly_platform_profit'] = monthly_platform_profit
        
        # داده‌های نمودار درآمد ماهانه (12 ماه گذشته)
        monthly_data = []
        for i in range(11, -1, -1):
            month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            revenue = paid_enrollments.filter(
                enrolled_at__gte=month_start,
                enrolled_at__lt=month_end
            ).aggregate(total=Sum('amount_paid'))['total'] or 0
            
            monthly_data.append(str(revenue))
        
        context['monthly_revenue_data'] = ', '.join(monthly_data)
        
        # وضعیت پرداخت‌ها
        paid_amount = paid_enrollments.aggregate(total=Sum('amount_paid'))['total'] or 0
        unpaid_amount = pending_enrollments.aggregate(total=Sum('amount_paid'))['total'] or 0
        
        context['paid_amount'] = paid_amount
        context['unpaid_amount'] = unpaid_amount
        
        # برترین معلمان از نظر درآمد
        from django.db.models import Count
        top_teachers = Teacher.objects.filter(
            is_active=True
        ).select_related('user').annotate(
            total_revenue=Sum('courses__enrollments__amount_paid', 
                            filter=Q(courses__enrollments__payment_status='paid')),
            course_count=Count('courses', filter=Q(courses__is_active=True)),
            successful_enrollments=Count('courses__enrollments',
                                        filter=Q(courses__enrollments__payment_status='paid'))
        ).filter(total_revenue__gt=0).order_by('-total_revenue')[:10]
        
        context['top_teachers'] = top_teachers
        
        # پردرآمدترین دوره‌ها
        top_courses = Course.objects.filter(
            is_active=True
        ).select_related('teacher__user').annotate(
            total_revenue=Sum('enrollments__amount_paid',
                            filter=Q(enrollments__payment_status='paid')),
            enrollment_count=Count('enrollments')
        ).filter(total_revenue__gt=0).order_by('-total_revenue')[:10]
        
        context['top_courses'] = top_courses
        
        return context


class AdminApplicationsListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """لیست درخواست‌های همکاری معلمان"""
    template_name = 'dashboard/admin_applications.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        status = self.request.GET.get('status', 'all')
        
        applications = TeacherApplication.objects.all()
        
        if status != 'all':
            applications = applications.filter(status=status)
        
        # Pagination
        from django.core.paginator import Paginator
        applications_ordered = applications.order_by('-submitted_at')
        paginator = Paginator(applications_ordered, 10)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context['applications'] = page_obj
        context['status_filter'] = status
        
        return context


class AdminCourseRequestsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """لیست درخواست‌های دوره"""
    template_name = 'dashboard/admin_course_requests.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import CourseRequest
        
        status = self.request.GET.get('status', 'all')
        
        requests = CourseRequest.objects.select_related('user').all()
        
        if status != 'all':
            requests = requests.filter(status=status)
        
        # Pagination
        from django.core.paginator import Paginator
        requests_ordered = requests.order_by('-created_at')
        paginator = Paginator(requests_ordered, 10)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context['requests'] = page_obj
        context['status_filter'] = status
        context['pending_count'] = CourseRequest.objects.filter(status='pending').count()
        
        return context


class AdminConsultationRequestsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """لیست درخواست‌های مشاوره"""
    template_name = 'dashboard/admin_consultation_requests.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import ConsultationRequest
        
        status = self.request.GET.get('status', 'all')
        
        requests = ConsultationRequest.objects.select_related('user', 'consultant').all()
        
        if status != 'all':
            requests = requests.filter(status=status)
        
        # Pagination
        from django.core.paginator import Paginator
        requests_ordered = requests.order_by('-created_at')
        paginator = Paginator(requests_ordered, 10)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context['requests'] = page_obj
        context['status_filter'] = status
        context['pending_count'] = ConsultationRequest.objects.filter(status='pending').count()
        
        return context


class AdminLoginHistoryView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """تاریخچه ورود کاربران"""
    template_name = 'dashboard/admin_login_history.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import LoginHistory
        
        user_filter = self.request.GET.get('user', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        
        history = LoginHistory.objects.select_related('user').all()
        
        if user_filter:
            history = history.filter(
                Q(user__email__icontains=user_filter) |
                Q(user__first_name__icontains=user_filter) |
                Q(user__last_name__icontains=user_filter)
            )
        
        if date_from:
            history = history.filter(login_time__gte=date_from)
        
        if date_to:
            history = history.filter(login_time__lte=date_to)
        
        context['history'] = history.order_by('-login_time')[:100]
        context['user_filter'] = user_filter
        context['date_from'] = date_from
        context['date_to'] = date_to
        context['total_logins'] = LoginHistory.objects.count()
        context['today_logins'] = LoginHistory.objects.filter(
            login_time__date=timezone.now().date()
        ).count()
        
        return context


class AdminSessionsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """مدیریت نشست‌های فعال"""
    template_name = 'dashboard/admin_sessions.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.sessions.models import Session
        from .models import LoginHistory
        
        # نشست‌های فعال
        active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        
        # اطلاعات تکمیلی از LoginHistory
        session_data = []
        for session in active_sessions:
            try:
                login_history = LoginHistory.objects.filter(
                    session_key=session.session_key,
                    logout_time__isnull=True
                ).select_related('user').first()
                
                if login_history:
                    session_data.append({
                        'session': session,
                        'user': login_history.user,
                        'login_time': login_history.login_time,
                        'ip_address': login_history.ip_address,
                        'device_type': login_history.device_type,
                        'browser': login_history.browser,
                    })
            except:
                pass
        
        context['sessions'] = session_data
        context['total_sessions'] = len(session_data)
        
        return context


class AdminPermissionsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """مدیریت دسترسی‌ها و نقش‌ها"""
    template_name = 'dashboard/admin_permissions.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.auth.models import Group, Permission
        
        context['users'] = User.objects.all().order_by('-date_joined')
        context['groups'] = Group.objects.all()
        context['superusers'] = User.objects.filter(is_superuser=True).count()
        context['staff_users'] = User.objects.filter(is_staff=True).count()
        
        return context


class AdminSecuritySettingsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """تنظیمات امنیتی سیستم"""
    template_name = 'dashboard/admin_security_settings.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import SecuritySettings
        
        context['settings'] = SecuritySettings.get_settings()
        
        return context
    
    def post(self, request, *args, **kwargs):
        from .models import SecuritySettings
        
        settings = SecuritySettings.get_settings()
        
        # Update settings
        settings.min_password_length = int(request.POST.get('min_password_length', 8))
        settings.require_uppercase = request.POST.get('require_uppercase') == 'on'
        settings.require_lowercase = request.POST.get('require_lowercase') == 'on'
        settings.require_numbers = request.POST.get('require_numbers') == 'on'
        settings.require_special_chars = request.POST.get('require_special_chars') == 'on'
        settings.password_expiry_days = int(request.POST.get('password_expiry_days', 0))
        settings.session_timeout_minutes = int(request.POST.get('session_timeout_minutes', 60))
        settings.max_concurrent_sessions = int(request.POST.get('max_concurrent_sessions', 3))
        settings.max_login_attempts = int(request.POST.get('max_login_attempts', 5))
        settings.lockout_duration_minutes = int(request.POST.get('lockout_duration_minutes', 30))
        settings.enable_2fa = request.POST.get('enable_2fa') == 'on'
        settings.force_2fa_for_admins = request.POST.get('force_2fa_for_admins') == 'on'
        settings.enable_email_verification = request.POST.get('enable_email_verification') == 'on'
        settings.log_failed_attempts = request.POST.get('log_failed_attempts') == 'on'
        settings.updated_by = request.user
        
        settings.save()
        
        messages.success(request, 'تنظیمات امنیتی با موفقیت بروزرسانی شد.')
        return redirect('dashboard:admin_security_settings')


class AdminTeacherRegisterView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """ثبت‌نام دستی معلم توسط ادمین"""
    template_name = 'dashboard/admin_teacher_register.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def post(self, request, *args, **kwargs):
        from account.forms import TeacherRegistrationForm
        
        # ساخت یک TeacherApplication موقت
        email = request.POST.get('email')
        
        # بررسی ایمیل تکراری
        if User.objects.filter(email=email).exists():
            messages.error(request, 'این ایمیل قبلاً ثبت شده است.')
            return redirect('dashboard:admin_teacher_register')
        
        # ایجاد یوزر و معلم
        try:
            user = User.objects.create_user(
                email=email,
                password=request.POST.get('password'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                user_type='teacher',
                is_active=True,
                is_email_verified=True
            )
            
            teacher = Teacher.objects.create(
                user=user,
                bio=request.POST.get('bio', ''),
                phone_number=request.POST.get('phone', ''),
                specialization=request.POST.get('specialization', ''),
                experience_years=request.POST.get('experience_years', 0)
            )
            
            messages.success(request, f'معلم {user.get_full_name()} با موفقیت ثبت شد.')
            return redirect('dashboard:admin_users')
            
        except Exception as e:
            messages.error(request, f'خطا در ثبت معلم: {str(e)}')
            return redirect('dashboard:admin_teacher_register')


class AdminStudentRegisterView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """ثبت‌نام دستی زبان‌آموز توسط ادمین"""
    template_name = 'dashboard/admin_student_register.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        
        # بررسی ایمیل تکراری
        if User.objects.filter(email=email).exists():
            messages.error(request, 'این ایمیل قبلاً ثبت شده است.')
            return redirect('dashboard:admin_student_register')
        
        # ایجاد یوزر و زبان‌آموز
        try:
            user = User.objects.create_user(
                email=email,
                password=request.POST.get('password'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                user_type='student',
                is_active=True,
                is_email_verified=True
            )
            
            student = Student.objects.create(
                user=user,
                phone_number=request.POST.get('phone', ''),
                english_level=request.POST.get('current_level', ''),
                goals=request.POST.get('learning_goal', '')
            )
            
            messages.success(request, f'زبان‌آموز {user.get_full_name()} با موفقیت ثبت شد.')
            return redirect('dashboard:admin_users')
            
        except Exception as e:
            messages.error(request, f'خطا در ثبت زبان‌آموز: {str(e)}')
            return redirect('dashboard:admin_student_register')


@login_required
def delete_session(request, session_key):
    """حذف نشست"""
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, 'دسترسی غیرمجاز.')
        return redirect('dashboard:admin_calendar')
    
    from django.contrib.sessions.models import Session
    from .models import LoginHistory
    
    try:
        session = Session.objects.get(session_key=session_key)
        session.delete()
        
        # بروزرسانی LoginHistory
        LoginHistory.objects.filter(
            session_key=session_key,
            logout_time__isnull=True
        ).update(logout_time=timezone.now())
        
        messages.success(request, 'نشست با موفقیت حذف شد.')
    except Session.DoesNotExist:
        messages.error(request, 'نشست یافت نشد.')
    
    return redirect('dashboard:admin_sessions')


class AdminEnrollmentDetailView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """صفحه جزئیات ثبت‌نام برای ادمین با امکان تأیید/رد"""
    template_name = 'dashboard/admin_enrollment_detail.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, 'دسترسی غیرمجاز.')
        return redirect('dashboard:dashboard_home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrollment_id = kwargs.get('enrollment_id')
        
        enrollment = get_object_or_404(
            Enrollment.objects.select_related(
                'student__user', 'course', 'course__teacher__user', 'course__category'
            ).prefetch_related('history'),
            id=enrollment_id
        )
        
        context['enrollment'] = enrollment
        context['student'] = enrollment.student
        context['course'] = enrollment.course
        
        return context


@login_required
@require_http_methods(["POST"])
def admin_approve_enrollment(request, enrollment_id):
    """تأیید ثبت‌نام توسط ادمین"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'دسترسی غیرمجاز.'}, status=403)
    
    try:
        from enrollment.models import Enrollment, EnrollmentHistory
        from django.contrib.auth.models import User as DjangoUser
        
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        
        # بررسی وضعیت فعلی
        if enrollment.status == 'confirmed':
            return JsonResponse({
                'success': False,
                'message': 'این ثبت‌نام قبلاً تأیید شده است.'
            })
        
        # بررسی ظرفیت دوره (فقط confirmed ها را حساب می‌کنیم)
        confirmed_count = enrollment.course.enrollments.filter(status='confirmed').count()
        if confirmed_count >= enrollment.course.capacity:
            return JsonResponse({
                'success': False,
                'message': 'ظرفیت دوره تکمیل شده است.'
            })
        
        # تأیید ثبت‌نام
        old_status = enrollment.status
        enrollment.status = 'confirmed'
        enrollment.confirmed_at = timezone.now()
        
        # به‌روزرسانی وضعیت پرداخت
        # اگر دوره رایگان است، وضعیت پرداخت را paid می‌کنیم
        # اگر دوره غیر رایگان است و فیش آپلود شده، paid می‌کنیم
        if enrollment.course.is_free:
            enrollment.payment_status = 'paid'
        elif enrollment.payment_receipt:
            enrollment.payment_status = 'paid'
            enrollment.amount_paid = enrollment.course.price
        
        enrollment.save()
        
        # ثبت تاریخچه
        EnrollmentHistory.objects.create(
            enrollment=enrollment,
            old_status=old_status,
            new_status='confirmed',
            changed_by=request.user.email,
            reason='تأیید توسط مدیریت'
        )
        
        # ارسال پیام موفقیت به داشبورد زبان‌آموز
        from django.contrib.sessions.models import Session
        from django.contrib import messages as django_messages
        
        # پیدا کردن session های فعال کاربر
        user_sessions = Session.objects.filter(
            expire_date__gte=timezone.now()
        )
        
        for session in user_sessions:
            session_data = session.get_decoded()
            if session_data.get('_auth_user_id') == str(enrollment.student.user.id):
                # اضافه کردن پیام به session
                session_data.setdefault('_messages', [])
                from django.contrib.messages.storage.base import Message
                msg = {
                    'message': f'تبریک! ثبت‌نام شما در دوره "{enrollment.course.title}" توسط مدیریت تأیید شد.',
                    'level': 25,  # SUCCESS
                    'extra_tags': 'enrollment',
                }
                # Note: این روش ساده‌تر است که message را در دیتابیس ذخیره کنیم
                # یا از notification system استفاده کنیم
        
        logger.info(f"Enrollment {enrollment_id} approved by admin {request.user.email}")
        
        return JsonResponse({
            'success': True,
            'message': 'ثبت‌نام با موفقیت تأیید شد.',
            'enrollment_status': enrollment.get_status_display(),
            'available_seats': enrollment.course.available_seats
        })
        
    except Exception as e:
        logger.error(f"Error approving enrollment {enrollment_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'خطا در تأیید ثبت‌نام: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def admin_reject_enrollment(request, enrollment_id):
    """رد ثبت‌نام توسط ادمین"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'دسترسی غیرمجاز.'}, status=403)
    
    try:
        from enrollment.models import Enrollment, EnrollmentHistory
        import json
        
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        
        # دریافت دلیل رد از request
        data = json.loads(request.body) if request.body else {}
        reject_reason = data.get('reason', 'عدم تأیید توسط مدیریت')
        
        # بررسی وضعیت فعلی
        if enrollment.status == 'cancelled':
            return JsonResponse({
                'success': False,
                'message': 'این ثبت‌نام قبلاً لغو شده است.'
            })
        
        # رد ثبت‌نام (بدون تأثیر روی ظرفیت)
        old_status = enrollment.status
        enrollment.status = 'cancelled'
        enrollment.cancelled_at = timezone.now()
        enrollment.admin_note = f"{enrollment.admin_note}\n\nرد شده: {reject_reason}" if enrollment.admin_note else f"رد شده: {reject_reason}"
        enrollment.save()
        
        # ثبت تاریخچه
        EnrollmentHistory.objects.create(
            enrollment=enrollment,
            old_status=old_status,
            new_status='cancelled',
            changed_by=request.user.email,
            reason=reject_reason
        )
        
        logger.info(f"Enrollment {enrollment_id} rejected by admin {request.user.email}")
        
        return JsonResponse({
            'success': True,
            'message': 'ثبت‌نام رد شد.',
            'enrollment_status': enrollment.get_status_display()
        })
        
    except Exception as e:
        logger.error(f"Error rejecting enrollment {enrollment_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'خطا در رد ثبت‌نام: {str(e)}'
        }, status=500)


class AdminApplicationDetailView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """صفحه جزئیات درخواست همکاری برای ادمین"""
    template_name = 'dashboard/admin_application_detail.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, 'دسترسی غیرمجاز.')
        return redirect('dashboard:dashboard_home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        application_id = kwargs.get('application_id')
        
        application = get_object_or_404(TeacherApplication, id=application_id)
        
        context['application'] = application
        
        return context


@login_required
@require_http_methods(["POST"])
def admin_approve_application(request, application_id):
    """تأیید درخواست همکاری توسط ادمین"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'دسترسی غیرمجاز.'}, status=403)
    
    try:
        application = get_object_or_404(TeacherApplication, id=application_id)
        
        if application.status == 'approved':
            return JsonResponse({
                'success': False,
                'message': 'این درخواست قبلاً تأیید شده است.'
            })
        
        # تأیید درخواست
        application.status = 'approved'
        application.reviewed_at = timezone.now()
        application.reviewed_by = request.user
        application.save()
        
        logger.info(f"Teacher application {application_id} approved by admin {request.user.email}")
        
        return JsonResponse({
            'success': True,
            'message': 'درخواست همکاری با موفقیت تأیید شد. معلم می‌تواند حساب کاربری خود را ایجاد کند.',
            'application_status': application.get_status_display()
        })
        
    except Exception as e:
        logger.error(f"Error approving application {application_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'خطا در تأیید درخواست: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def admin_reject_application(request, application_id):
    """رد درخواست همکاری توسط ادمین"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'دسترسی غیرمجاز.'}, status=403)
    
    try:
        import json
        
        application = get_object_or_404(TeacherApplication, id=application_id)
        
        # دریافت دلیل رد
        data = json.loads(request.body) if request.body else {}
        reject_reason = data.get('reason', 'عدم تأیید توسط مدیریت')
        
        if application.status == 'rejected':
            return JsonResponse({
                'success': False,
                'message': 'این درخواست قبلاً رد شده است.'
            })
        
        # رد درخواست
        application.status = 'rejected'
        application.reviewed_at = timezone.now()
        application.reviewed_by = request.user
        application.admin_notes = f"{application.admin_notes}\n\nرد شده: {reject_reason}" if application.admin_notes else f"رد شده: {reject_reason}"
        application.save()
        
        logger.info(f"Teacher application {application_id} rejected by admin {request.user.email}")
        
        return JsonResponse({
            'success': True,
            'message': 'درخواست همکاری رد شد.',
            'application_status': application.get_status_display()
        })
        
    except Exception as e:
        logger.error(f"Error rejecting application {application_id}: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'خطا در رد درخواست: {str(e)}'
        }, status=500)


class AdminLevelAssessmentRequestsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """لیست درخواست‌های تعیین سطح"""
    template_name = 'dashboard/admin_level_assessment_requests.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        search_query = self.request.GET.get('search', '')
        
        requests = DeterminationRequest.objects.all()
        
        if search_query:
            requests = requests.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query)
            )
        
        # Pagination
        from django.core.paginator import Paginator
        requests_ordered = requests.order_by('-submitted_at')
        paginator = Paginator(requests_ordered, 10)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context['requests'] = page_obj
        context['search_query'] = search_query
        context['total_requests'] = DeterminationRequest.objects.count()
        
        return context


class AdminLevelAssessmentDetailView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """صفحه جزئیات درخواست تعیین سطح"""
    template_name = 'dashboard/admin_level_assessment_detail.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, 'دسترسی غیرمجاز.')
        return redirect('dashboard:dashboard_home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_id = kwargs.get('request_id')
        
        assessment_request = get_object_or_404(DeterminationRequest, id=request_id)
        
        context['assessment_request'] = assessment_request
        
        return context


class AdminUserDetailView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """صفحه جزئیات کاربر برای ادمین"""
    template_name = 'dashboard/admin_user_detail.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, 'دسترسی غیرمجاز.')
        return redirect('dashboard:dashboard_home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = kwargs.get('user_id')
        
        user = get_object_or_404(User, id=user_id)
        
        context['user_detail'] = user
        
        # Get related data
        if user.user_type == 'student':
            try:
                context['student'] = Student.objects.get(user=user)
                context['enrollments'] = Enrollment.objects.filter(student=context['student']).select_related('course')[:5]
            except Student.DoesNotExist:
                context['student'] = None
        elif user.user_type == 'teacher':
            try:
                context['teacher'] = Teacher.objects.get(user=user)
                context['courses'] = Course.objects.filter(teacher=context['teacher'])[:5]
            except Teacher.DoesNotExist:
                context['teacher'] = None
        
        return context


class AdminCourseDetailView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """صفحه جزئیات دوره برای ادمین"""
    template_name = 'dashboard/admin_course_detail.html'
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, 'دسترسی غیرمجاز.')
        return redirect('dashboard:dashboard_home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = kwargs.get('course_id')
        
        course = get_object_or_404(
            Course.objects.select_related('teacher__user', 'category'),
            id=course_id
        )
        
        context['course'] = course
        
        # Get enrollments
        enrollments = Enrollment.objects.filter(course=course).select_related('student__user')
        context['enrollments'] = enrollments.order_by('-enrolled_at')[:10]
        context['total_enrollments'] = enrollments.count()
        context['confirmed_enrollments'] = enrollments.filter(status='confirmed').count()
        context['pending_enrollments'] = enrollments.filter(status='pending').count()
        
        return context


class AdminPrivateClassRequestsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """لیست درخواست‌های کلاس خصوصی"""
    template_name = 'dashboard/admin_private_class_requests.html'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import PrivateClassRequest
        
        status = self.request.GET.get('status', 'all')
        
        requests = PrivateClassRequest.objects.all()
        
        if status != 'all':
            requests = requests.filter(status=status)
        
        # Pagination
        from django.core.paginator import Paginator
        requests_ordered = requests.order_by('-created_at')
        paginator = Paginator(requests_ordered, 10)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context['requests'] = page_obj
        context['status_filter'] = status
        context['pending_count'] = PrivateClassRequest.objects.filter(status='pending').count()
        context['contacted_count'] = PrivateClassRequest.objects.filter(status='contacted').count()
        context['approved_count'] = PrivateClassRequest.objects.filter(status='approved').count()
        
        return context


class AdminPrivateClassRequestDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """جزئیات درخواست کلاس خصوصی"""
    template_name = 'dashboard/admin_private_class_request_detail.html'
    context_object_name = 'request_obj'
    pk_url_kwarg = 'request_id'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_queryset(self):
        from core.models import PrivateClassRequest
        return PrivateClassRequest.objects.all()
    
    def post(self, request, *args, **kwargs):
        """بروزرسانی وضعیت درخواست"""
        self.object = self.get_object()
        
        action = request.POST.get('action')
        admin_note = request.POST.get('admin_note', '')
        
        if action in ['contacted', 'approved', 'rejected']:
            self.object.status = action
            if admin_note:
                self.object.admin_note = admin_note
            self.object.save()
            
            messages.success(request, f'وضعیت درخواست به "{self.object.get_status_display()}" تغییر یافت.')
        
        return redirect('dashboard:admin_private_class_request_detail', request_id=self.object.id)


class AdminContactMessagesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """لیست پیام‌های پشتیبانی"""
    template_name = 'dashboard/admin_contact_messages.html'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import ContactMessage
        
        status = self.request.GET.get('status', 'all')
        
        messages_qs = ContactMessage.objects.all()
        
        if status != 'all':
            messages_qs = messages_qs.filter(status=status)
        
        # Pagination
        from django.core.paginator import Paginator
        messages_ordered = messages_qs.order_by('-created_at')
        paginator = Paginator(messages_ordered, 10)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context['messages'] = page_obj
        context['status_filter'] = status
        context['new_count'] = ContactMessage.objects.filter(status='new').count()
        context['read_count'] = ContactMessage.objects.filter(status='read').count()
        context['replied_count'] = ContactMessage.objects.filter(status='replied').count()
        
        return context


class AdminContactMessageDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """جزئیات و پاسخ به پیام پشتیبانی"""
    template_name = 'dashboard/admin_contact_message_detail.html'
    context_object_name = 'message'
    pk_url_kwarg = 'message_id'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_queryset(self):
        from core.models import ContactMessage
        return ContactMessage.objects.all()
    
    def get_object(self):
        obj = super().get_object()
        # علامت‌گذاری به عنوان خوانده شده
        if obj.status == 'new':
            obj.status = 'read'
            obj.save()
        return obj
    
    def post(self, request, *args, **kwargs):
        """ارسال پاسخ به پیام"""
        self.object = self.get_object()
        
        reply_text = request.POST.get('reply', '').strip()
        
        if reply_text:
            from django.utils import timezone
            self.object.reply = reply_text
            self.object.replied_by = request.user
            self.object.replied_at = timezone.now()
            self.object.status = 'replied'
            self.object.save()
            
            messages.success(request, 'پاسخ شما با موفقیت ثبت شد.')
        else:
            messages.error(request, 'لطفاً متن پاسخ را وارد کنید.')
        
        return redirect('dashboard:admin_contact_message_detail', message_id=self.object.id)


class AdminCalendarView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """تقویم ادمین - نمایش همه رویدادها"""
    template_name = 'dashboard/admin_calendar.html'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import CalendarEvent
        from course.models import Course, Assignment, Exam
        
        # دریافت تمام رویدادها
        events = []
        
        # رویدادهای تقویم
        calendar_events = CalendarEvent.objects.all()
        for event in calendar_events:
            events.append({
                'id': f'event-{event.id}',
                'title': event.title,
                'start': event.start_datetime.isoformat(),
                'end': event.end_datetime.isoformat() if event.end_datetime else None,
                'color': event.color,
                'type': event.event_type,
            })
        
        # کلاس‌ها
        courses = Course.objects.filter(is_active=True, status='published')
        for course in courses:
            if course.start_date:
                events.append({
                    'id': f'course-{course.id}',
                    'title': f'🎓 {course.title}',
                    'start': course.start_date.isoformat(),
                    'end': course.end_date.isoformat() if course.end_date else None,
                    'color': '#4CAF50',
                    'type': 'class',
                })
        
        # تکالیف
        assignments = Assignment.objects.filter(is_active=True)
        for assignment in assignments:
            events.append({
                'id': f'assignment-{assignment.id}',
                'title': f'📝 {assignment.title}',
                'start': assignment.due_date.isoformat(),
                'color': '#2196F3',
                'type': 'assignment',
            })
        
        # امتحانات
        exams = Exam.objects.filter(is_active=True)
        for exam in exams:
            color = '#F44336' if exam.exam_type == 'final' else '#FF5722' if exam.exam_type == 'midterm' else '#9C27B0'
            events.append({
                'id': f'exam-{exam.id}',
                'title': f'📊 {exam.title}',
                'start': exam.scheduled_start.isoformat(),
                'end': exam.scheduled_end.isoformat(),
                'color': color,
                'type': 'exam',
            })
        
        context['events_json'] = json.dumps(events)
        return context


class StudentCalendarView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """تقویم زبان‌آموز - نمایش کلاس‌ها و تکالیف"""
    template_name = 'dashboard/student_calendar.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'user_type') and self.request.user.user_type == 'student'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from account.models import Student
        from enrollment.models import Enrollment
        from course.models import Assignment
        
        try:
            student = Student.objects.get(user=self.request.user)
        except Student.DoesNotExist:
            context['events_json'] = json.dumps([])
            return context
        
        events = []
        
        # کلاس‌های ثبت‌نام شده
        enrollments = Enrollment.objects.filter(student=student, status='confirmed').select_related('course')
        for enrollment in enrollments:
            course = enrollment.course
            if course.start_date:
                events.append({
                    'id': f'course-{course.id}',
                    'title': f'🎓 {course.title}',
                    'start': course.start_date.isoformat(),
                    'end': course.end_date.isoformat() if course.end_date else None,
                    'color': '#4CAF50',
                    'type': 'class',
                    'url': f'/courses/student-course/{course.id}/'
                })
        
        # تکالیف دوره‌های ثبت‌نام شده
        course_ids = enrollments.values_list('course_id', flat=True)
        assignments = Assignment.objects.filter(course_id__in=course_ids, is_active=True)
        for assignment in assignments:
            events.append({
                'id': f'assignment-{assignment.id}',
                'title': f'📝 {assignment.title} ({assignment.course.title})',
                'start': assignment.due_date.isoformat(),
                'color': '#2196F3',
                'type': 'assignment',
            })
        
        # امتحانات دوره‌های ثبت‌نام شده
        from course.models import Exam
        exams = Exam.objects.filter(course_id__in=course_ids, is_active=True)
        for exam in exams:
            # فقط امتحانات قابل رویت را نمایش بده
            can_see, _ = exam.can_student_see(student)
            if can_see:
                color = '#F44336' if exam.exam_type == 'final' else '#FF5722' if exam.exam_type == 'midterm' else '#9C27B0'
                events.append({
                    'id': f'exam-{exam.id}',
                    'title': f'📊 {exam.title}',
                    'start': exam.scheduled_start.isoformat(),
                    'end': exam.scheduled_end.isoformat(),
                    'color': color,
                    'type': 'exam',
                })
        
        context['events_json'] = json.dumps(events)
        return context


@login_required
def export_financial_pdf(request):
    """تولید گزارش مالی به صورت PDF"""
    if not request.user.is_superuser:
        messages.error(request, 'شما دسترسی لازم برای این عملیات را ندارید.')
        return redirect('dashboard:admin_calendar')
    
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    from decimal import Decimal
    import jdatetime
    
    # دریافت فیلترها
    teacher_filter = request.GET.get('teacher', 'all')
    course_filter = request.GET.get('course', 'all')
    payment_filter = request.GET.get('payment_status', 'all')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')
    
    # تراکنش‌ها
    transactions = Enrollment.objects.select_related(
        'student__user', 'course', 'course__teacher__user'
    ).all()
    
    # اعمال فیلترها
    if teacher_filter != 'all':
        transactions = transactions.filter(course__teacher__id=teacher_filter)
    
    if course_filter != 'all':
        transactions = transactions.filter(course__id=course_filter)
    
    if payment_filter != 'all':
        transactions = transactions.filter(payment_status=payment_filter)
    
    if from_date:
        transactions = transactions.filter(enrolled_at__gte=from_date)
    
    if to_date:
        transactions = transactions.filter(enrolled_at__lte=to_date)
    
    transactions = transactions.order_by('-enrolled_at')
    
    # محاسبات مالی
    paid_enrollments = Enrollment.objects.filter(payment_status='paid')
    total_revenue = paid_enrollments.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0')
    teacher_share = total_revenue * Decimal('0.7')
    platform_profit = total_revenue * Decimal('0.3')
    
    # محاسبه مجموع تراکنش‌های فیلتر شده
    filtered_total = transactions.filter(payment_status='paid').aggregate(
        total=Sum('amount_paid')
    )['total'] or Decimal('0')
    
    # تاریخ فارسی
    now = jdatetime.datetime.now()
    jalali_date = now.strftime('%Y/%m/%d - %H:%M')
    
    context = {
        'transactions': transactions,
        'total_revenue': total_revenue,
        'teacher_share': teacher_share,
        'platform_profit': platform_profit,
        'filtered_total': filtered_total,
        'jalali_date': jalali_date,
        'total_count': transactions.count(),
    }
    
    # رندر template
    html_string = render_to_string('dashboard/financial_report_pdf.html', context)
    
    # تولید PDF با WeasyPrint
    try:
        from weasyprint import HTML
        
        # ایجاد PDF
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
        pdf = pdf_file.write_pdf()
        
        # ارسال response
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="financial_report_{now.strftime("%Y%m%d_%H%M")}.pdf"'
        return response
        
    except ImportError:
        messages.error(request, 'برای تولید PDF باید کتابخانه WeasyPrint نصب شود: pip install weasyprint')
        return redirect('dashboard:admin_financial')
