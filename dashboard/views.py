from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView

from account.models import Student, Teacher


class DashboardView(LoginRequiredMixin, TemplateView):
    """Universal dashboard that redirects to appropriate user dashboard"""

    def get(self, request, *args, **kwargs):
        user = request.user

        if user.user_type == 'student':
            student = get_object_or_404(Student, user=user)
            return redirect('dashboard:student_dashboard', student_id=student.id)
        elif user.user_type == 'teacher':
            return redirect('dashboard:teacher_dashboard')
        elif user.user_type == 'admin':
            return redirect('admin:index')
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
        try:
            _ = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            if request.user.user_type == 'student':
                Student.objects.create(user=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = get_object_or_404(Student, id=kwargs['student_id'])
        context['student'] = student

        from enrollment.models import Enrollment
        from course.models import Course

        enrollments = Enrollment.objects.filter(student=student).select_related('course', 'course__teacher', 'course__category').order_by('-enrolled_at')
        context['enrollments'] = enrollments
        context['total_enrollments'] = enrollments.count()
        context['confirmed_enrollments'] = enrollments.filter(status='confirmed').count()
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
            'active_courses': enrollments.filter(status='confirmed').count(),
            'pending_courses': enrollments.filter(status='pending').count(),
            'completed_courses': enrollments.filter(status='completed').count(),
        }

        enrolled_course_ids = enrollments.filter(
            status__in=['pending', 'confirmed']
        ).values_list('course_id', flat=True)
        available_courses = Course.objects.filter(
            is_active=True,
            status='published'
        ).exclude(id__in=enrolled_course_ids).select_related(
            'teacher__user', 'category'
        ).order_by('-created_at')[:6]
        context['available_courses'] = available_courses

        try:
            from account.models import PageContent
            dashboard_content = PageContent.objects.get(page_type='student_dashboard', is_active=True)
            context['dashboard_content'] = dashboard_content
        except Exception:
            context['dashboard_content'] = None

        total_confirmed = context['confirmed_enrollments'] + context['completed_enrollments']
        if total_confirmed > 0:
            context['learning_progress'] = {
                'completion_rate': int((context['completed_enrollments'] / total_confirmed) * 100),
                'active_rate': int((context['confirmed_enrollments'] / total_confirmed) * 100),
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
        return redirect('dashboard:index')

    def dispatch(self, request, *args, **kwargs):
        try:
            _ = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
            if request.user.user_type == 'teacher':
                messages.error(request, 'حساب مدرس شما هنوز تکمیل/تایید نشده است. لطفاً پس از تایید ادمین ثبت‌نام مدرس را تکمیل کنید.')
                return redirect('account:teacher_apply')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = get_object_or_404(Teacher, user=self.request.user)
        context['teacher'] = teacher

        from course.models import Course
        from enrollment.models import Enrollment
        from django.utils import timezone
        from datetime import datetime, timedelta
        from django.db.models import Count, Sum, Avg

        courses = Course.objects.filter(teacher=teacher.pk, is_active=True).select_related('category')
        context['courses'] = courses

        total_students = sum(course.enrolled_count for course in courses)
        context['total_students'] = total_students

        recent_enrollments = Enrollment.objects.filter(
            course__teacher=teacher.pk
        ).select_related('student__user', 'course').order_by('-enrolled_at')[:5]
        context['recent_enrollments'] = recent_enrollments

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
