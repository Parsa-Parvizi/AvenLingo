from django.contrib.auth.views import TemplateView
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse_lazy
from django.utils import timezone
from course.models import Course, Assignment, AssignmentSubmission
from account.models import Teacher
from course.forms import CourseForm, AssignmentForm
from enrollment.models import Enrollment


class TeacherDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teacher/teacher_dashboard.html'

    def test_func(self):
        return self.request.user.groups.filter(name='Teachers').exists()


class TeacherCourseView(LoginRequiredMixin, View):
    def get(self, request):
        # Map logged-in user to Teacher profile
        teacher = get_object_or_404(Teacher, user=request.user)
        courses = Course.objects.filter(teacher=teacher).select_related('category')
        return render(request, 'teacher/teacher_courses.html', {'courses': courses})


class TeacherCourseStudentView(LoginRequiredMixin, View):
    def get(self, request, course_id):
        teacher = get_object_or_404(Teacher, user=request.user)
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        # Prefetch students; enrollment status rendering kept simple in template
        students = course.students.select_related('user').all()
        return render(request, 'teacher/teacher_course_students.html', {'course': course, 'students': students})

class TeacherScheduleView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teacher/schedule.html'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import CalendarEvent
        from course.models import Course, Assignment
        import json
        
        try:
            teacher = Teacher.objects.get(user=self.request.user)
        except Teacher.DoesNotExist:
            context['events_json'] = json.dumps([])
            return context
        
        events = []
        
        # کلاس‌های معلم
        courses = Course.objects.filter(teacher=teacher, is_active=True)
        for course in courses:
            if course.start_date:
                events.append({
                    'id': f'course-{course.id}',
                    'title': f'🎓 {course.title}',
                    'start': course.start_date.isoformat(),
                    'end': course.end_date.isoformat() if course.end_date else None,
                    'color': '#4CAF50',
                    'type': 'class',
                    'url': f'/teachers/courses/{course.id}/students/',
                })
        
        # تکالیف کلاس‌های معلم
        course_ids = courses.values_list('id', flat=True)
        assignments = Assignment.objects.filter(course_id__in=course_ids, is_active=True)
        for assignment in assignments:
            events.append({
                'id': f'assignment-{assignment.id}',
                'title': f'📝 {assignment.title}',
                'start': assignment.due_date.isoformat(),
                'color': '#FF9800',
                'type': 'assignment',
                'url': f'/teachers/assignments/{assignment.id}/',
            })
        
        # امتحانات کلاس‌های معلم
        from course.models import Exam
        exams = Exam.objects.filter(course_id__in=course_ids, is_active=True)
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
        
        # رویدادهای شخصی معلم
        personal_events = CalendarEvent.objects.filter(created_by=self.request.user)
        for event in personal_events:
            events.append({
                'id': f'event-{event.id}',
                'title': event.title,
                'start': event.start_datetime.isoformat(),
                'end': event.end_datetime.isoformat() if event.end_datetime else None,
                'color': event.color,
                'type': event.event_type,
            })
        
        context['events_json'] = json.dumps(events)
        context['teacher'] = teacher
        return context

class TeacherPerformanceView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teacher/performance.html'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'

class TeacherMessagesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teacher/messages.html'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'


class AllTeacherView(ListView):
    model = Teacher
    template_name = 'teacher/teacher_list.html'
    context_object_name = 'teachers'
    paginate_by = 10


class TeacherDetailView(DetailView):
    model = Teacher
    template_name = 'teacher/teacher_detail.html'
    context_object_name = 'teacher'
    pk_url_kwarg = 'teacher_id'

@method_decorator(login_required, name='dispatch')
class TeacherCreateCourseView(View):
    template_name = 'teacher/teacher_create_course.html'

    def get(self, request):
        form = CourseForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            teacher = get_object_or_404(Teacher, user=request.user)
            course.teacher = teacher
            course.save()
            messages.success(request, 'دوره با موفقیت ایجاد شد.')
            return render(request, self.template_name, {'form': CourseForm(), 'success': True})
        return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class TeacherEditCourseView(View):
    template_name = 'teacher/teacher_edit_course.html'

    def get(self, request, course_id):
        teacher = get_object_or_404(Teacher, user=request.user)
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        form = CourseForm(instance=course)
        return render(request, self.template_name, {'form': form, 'course': course})

    def post(self, request, course_id):
        teacher = get_object_or_404(Teacher, user=request.user)
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'دوره با موفقیت ویرایش شد.')
            return redirect('teacher:teacher_courses')
        return render(request, self.template_name, {'form': form, 'course': course})


# Assignment Views
@method_decorator(login_required, name='dispatch')
class TeacherAssignmentsView(View):
    """نمایش لیست تکالیف معلم"""
    template_name = 'teacher/teacher_assignments.html'

    def get(self, request, course_id=None):
        teacher = get_object_or_404(Teacher, user=request.user)
        
        if course_id:
            # نمایش تکالیف یک دوره خاص
            course = get_object_or_404(Course, id=course_id, teacher=teacher)
            assignments = Assignment.objects.filter(course=course, teacher=teacher).order_by('-created_at')
            context = {
                'assignments': assignments,
                'course': course,
                'single_course': True
            }
        else:
            # نمایش همه تکالیف معلم
            assignments = Assignment.objects.filter(teacher=teacher).select_related('course').order_by('-created_at')
            courses = Course.objects.filter(teacher=teacher).prefetch_related('assignments')
            context = {
                'assignments': assignments,
                'courses': courses,
                'single_course': False
            }
        
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class TeacherCreateAssignmentView(View):
    """ایجاد تکلیف جدید"""
    template_name = 'teacher/teacher_create_assignment.html'

    def get(self, request, course_id):
        teacher = get_object_or_404(Teacher, user=request.user)
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        
        # بررسی محدودیت تعداد تکالیف
        assignment_count = Assignment.objects.filter(course=course, teacher=teacher).count()
        if assignment_count >= 3:
            messages.error(request, 'حداکثر ۳ تکلیف برای هر دوره مجاز است.')
            return redirect('teacher:course_assignments', course_id=course_id)
        
        form = AssignmentForm()
        return render(request, self.template_name, {'form': form, 'course': course})

    def post(self, request, course_id):
        teacher = get_object_or_404(Teacher, user=request.user)
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        
        # بررسی محدودیت تعداد تکالیف
        assignment_count = Assignment.objects.filter(course=course, teacher=teacher).count()
        if assignment_count >= 3:
            messages.error(request, 'حداکثر ۳ تکلیف برای هر دوره مجاز است.')
            return redirect('teacher:course_assignments', course_id=course_id)
        
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.teacher = teacher
            assignment.course = course
            assignment.save()
            messages.success(request, 'تکلیف با موفقیت ایجاد شد.')
            return redirect('teacher:course_assignments', course_id=course_id)
        
        return render(request, self.template_name, {'form': form, 'course': course})


@method_decorator(login_required, name='dispatch')
class TeacherEditAssignmentView(View):
    """ویرایش تکلیف"""
    template_name = 'teacher/teacher_edit_assignment.html'

    def get(self, request, assignment_id):
        teacher = get_object_or_404(Teacher, user=request.user)
        assignment = get_object_or_404(Assignment, id=assignment_id, teacher=teacher)
        form = AssignmentForm(instance=assignment)
        return render(request, self.template_name, {'form': form, 'assignment': assignment})

    def post(self, request, assignment_id):
        teacher = get_object_or_404(Teacher, user=request.user)
        assignment = get_object_or_404(Assignment, id=assignment_id, teacher=teacher)
        form = AssignmentForm(request.POST, request.FILES, instance=assignment)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'تکلیف با موفقیت ویرایش شد.')
            return redirect('teacher:assignment_detail', assignment_id=assignment.id)
        
        return render(request, self.template_name, {'form': form, 'assignment': assignment})


@method_decorator(login_required, name='dispatch')
class TeacherDeleteAssignmentView(View):
    """حذف تکلیف"""

    def post(self, request, assignment_id):
        teacher = get_object_or_404(Teacher, user=request.user)
        assignment = get_object_or_404(Assignment, id=assignment_id, teacher=teacher)
        
        course_id = assignment.course.id
        assignment.delete()
        messages.success(request, 'تکلیف با موفقیت حذف شد.')
        
        return redirect('teacher:course_assignments', course_id=course_id)


@method_decorator(login_required, name='dispatch')
class TeacherAssignmentDetailView(View):
    """جزئیات تکلیف و مشاهده ارسال‌ها"""
    template_name = 'teacher/teacher_assignment_detail.html'

    def get(self, request, assignment_id):
        teacher = get_object_or_404(Teacher, user=request.user)
        assignment = get_object_or_404(Assignment, id=assignment_id, teacher=teacher)
        
        # دریافت ارسال‌های دانش‌آموزان
        submissions = AssignmentSubmission.objects.filter(
            assignment=assignment
        ).select_related('student__user').order_by('-submitted_at')
        
        context = {
            'assignment': assignment,
            'submissions': submissions,
            'submission_count': submissions.count(),
            'graded_count': submissions.filter(status='graded').count(),
            'pending_count': submissions.filter(status='submitted').count(),
        }
        
        return render(request, self.template_name, context)


# Additional Views
@method_decorator(login_required, name='dispatch')
class TeacherActivitiesView(View):
    """نمایش فعالیت‌های اخیر معلم"""
    template_name = 'teacher/teacher_activities.html'

    def get(self, request):
        teacher = get_object_or_404(Teacher, user=request.user)
        
        # شبیه‌سازی فعالیت‌ها (در آینده از مدل واقعی استفاده کنید)
        activities = [
            {
                'title': 'تکلیف جدید ایجاد شد',
                'description': 'تکلیف "تمرین گرامر" برای دوره "انگلیسی پیشرفته" ایجاد شد',
                'created_at': timezone.now() - timezone.timedelta(hours=2),
                'icon': 'fas fa-tasks',
                'type': 'assignment'
            },
            {
                'title': 'دانش‌آموز جدید ثبت‌نام کرد',
                'description': 'علی احمدی در دوره "انگلیسی مبتدی" ثبت‌نام کرد',
                'created_at': timezone.now() - timezone.timedelta(hours=5),
                'icon': 'fas fa-user-plus',
                'type': 'enrollment'
            },
            {
                'title': 'تکلیف تصحیح شد',
                'description': 'تکلیف "مقاله نگارش" توسط ۳ دانش‌آموز تصحیح شد',
                'created_at': timezone.now() - timezone.timedelta(days=1),
                'icon': 'fas fa-check-circle',
                'type': 'grading'
            },
            {
                'title': 'دوره جدید ایجاد شد',
                'description': 'دوره "آمادگی آیلتس" با موفقیت ایجاد شد',
                'created_at': timezone.now() - timezone.timedelta(days=2),
                'icon': 'fas fa-book',
                'type': 'course'
            },
        ]
        
        context = {
            'activities': activities,
            'teacher': teacher
        }
        
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class TeacherNotificationsView(View):
    """نمایش اعلانات معلم"""
    template_name = 'teacher/teacher_notifications.html'

    def get(self, request):
        teacher = get_object_or_404(Teacher, user=request.user)
        
        # شبیه‌سازی اعلانات (در آینده از مدل واقعی استفاده کنید)
        notifications = [
            {
                'title': 'تکلیف جدید ارسال شد',
                'description': 'دانش‌آموز مریم حسینی تکلیف "تمرین مکالمه" را ارسال کرد',
                'created_at': timezone.now() - timezone.timedelta(minutes=30),
                'icon': 'fas fa-upload',
                'type': 'info',
                'read': False
            },
            {
                'title': 'یادآوری تصحیح تکلیف',
                'description': '۳ تکلیف در انتظار تصحیح هستند',
                'created_at': timezone.now() - timezone.timedelta(hours=1),
                'icon': 'fas fa-clock',
                'type': 'warning',
                'read': False
            },
            {
                'title': 'دوره تأیید شد',
                'description': 'دوره "انگلیسی تجاری" توسط ادمین تأیید شد',
                'created_at': timezone.now() - timezone.timedelta(days=1),
                'icon': 'fas fa-check',
                'type': 'success',
                'read': True
            },
            {
                'title': 'سیستم به‌روزرسانی شد',
                'description': 'ویژگی‌های جدید سیستم تکالیف اضافه شد',
                'created_at': timezone.now() - timezone.timedelta(days=3),
                'icon': 'fas fa-info-circle',
                'type': 'info',
                'read': True
            },
        ]
        
        context = {
            'notifications': notifications,
            'teacher': teacher,
            'unread_count': len([n for n in notifications if not n['read']])
        }
        
        return render(request, self.template_name, context)


# These are defined earlier in the file - keeping for backwards compatibility