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
        from django.db.models import Sum
        # Map logged-in user to Teacher profile
        teacher = get_object_or_404(Teacher, user=request.user)
        courses = Course.objects.filter(teacher=teacher).select_related('category')
        
        # فیلترها
        search_query = request.GET.get('q', '')
        status_filter = request.GET.get('status', '')
        order_by = request.GET.get('order', '-created_at')
        
        if search_query:
            courses = courses.filter(title__icontains=search_query)
        
        if status_filter == 'active':
            courses = courses.filter(is_active=True, status='active')
        elif status_filter == 'upcoming':
            courses = courses.filter(status='upcoming')
        elif status_filter == 'completed':
            courses = courses.filter(status='completed')
        
        courses = courses.order_by(order_by)
        
        # آمار
        total_students = sum(course.enrolled_count for course in courses)
        total_revenue = courses.aggregate(
            total=Sum('price')
        )['total'] or 0
        
        context = {
            'courses': courses,
            'total_students': total_students,
            'total_revenue': total_revenue,
        }
        return render(request, 'teacher/teacher_courses.html', context)


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
class TeacherNotificationsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """نمایش اعلانات معلم"""
    template_name = 'teacher/teacher_notifications.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            teacher = Teacher.objects.get(user=self.request.user)
        except Teacher.DoesNotExist:
            context['notifications'] = []
            return context
        
        from course.models import AssignmentSubmission, Exam
        from enrollment.models import Enrollment
        from django.core.paginator import Paginator
        
        filter_type = self.request.GET.get('filter', 'all')
        
        # ایجاد اعلانات بر اساس داده‌های واقعی
        notifications = []
        
        # اعلان‌های ثبت‌نام جدید
        if filter_type in ['all', 'enrollment']:
            recent_enrollments = Enrollment.objects.filter(
                course__teacher=teacher,
                status='pending'
            ).select_related('student__user', 'course').order_by('-enrolled_at')[:10]
            
            for enrollment in recent_enrollments:
                notifications.append({
                    'title': 'ثبت‌نام جدید',
                    'message': f'{enrollment.student.user.get_full_name()} در دوره "{enrollment.course.title}" ثبت‌نام کرد',
                    'created_at': enrollment.enrolled_at,
                    'type': 'success',
                    'is_read': False,
                    'action_url': f'/dashboard/admin/enrollments/{enrollment.id}/',
                })
        
        # اعلان‌های تکلیف جدید ارسال شده
        if filter_type in ['all', 'assignment']:
            recent_submissions = AssignmentSubmission.objects.filter(
                assignment__course__teacher=teacher,
                graded_by__isnull=True
            ).select_related('student__user', 'assignment').order_by('-submitted_at')[:10]
            
            for submission in recent_submissions:
                notifications.append({
                    'title': 'تکلیف جدید ارسال شد',
                    'message': f'{submission.student.user.get_full_name()} تکلیف "{submission.assignment.title}" را ارسال کرد',
                    'created_at': submission.submitted_at,
                    'type': 'info',
                    'is_read': False,
                    'action_url': f'/teachers/assignments/{submission.assignment.id}/',
                })
        
        # اعلان‌های امتحان پیش رو
        if filter_type in ['all', 'exam']:
            today = timezone.now().date()
            upcoming_exams = Exam.objects.filter(
                course__teacher=teacher,
                date__gte=today,
                date__lte=today + timezone.timedelta(days=7)
            ).select_related('course').order_by('date')[:5]
            
            for exam in upcoming_exams:
                notifications.append({
                    'title': 'امتحان پیش رو',
                    'message': f'امتحان "{exam.title}" دوره "{exam.course.title}" در {exam.date}',
                    'created_at': timezone.now(),
                    'type': 'warning',
                    'is_read': False,
                    'action_url': f'/teachers/exams/{exam.id}/participants/',
                })
        
        # فیلتر unread
        if filter_type == 'unread':
            # همه اعلان‌ها به صورت پیش‌فرض unread هستند
            pass
        
        # مرتب‌سازی بر اساس تاریخ
        notifications.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Pagination
        paginator = Paginator(notifications, 20)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context['notifications'] = page_obj
        
        return context




# These are defined earlier in the file - keeping for backwards compatibility

# Exam Views
class TeacherExamsListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """لیست کل امتحانات معلم"""
    template_name = 'teacher/teacher_exams_list.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            teacher = Teacher.objects.get(user=self.request.user)
        except Teacher.DoesNotExist:
            return context
        
        from course.models import Exam
        from django.utils import timezone
        
        # فیلترها
        course_filter = self.request.GET.get('course', '')
        type_filter = self.request.GET.get('type', '')
        status_filter = self.request.GET.get('status', '')
        
        exams = Exam.objects.filter(course__teacher=teacher).select_related('course').order_by('-date')
        
        if course_filter:
            exams = exams.filter(course_id=course_filter)
        
        if type_filter:
            exams = exams.filter(exam_type=type_filter)
        
        today = timezone.now().date()
        if status_filter == 'upcoming':
            exams = exams.filter(date__gt=today)
        elif status_filter == 'ongoing':
            exams = exams.filter(date=today)
        elif status_filter == 'completed':
            exams = exams.filter(date__lt=today)
        
        # آمار
        context['exams'] = exams
        context['total_exams'] = exams.count()
        context['upcoming_exams'] = exams.filter(date__gt=today).count()
        context['completed_exams'] = exams.filter(date__lt=today).count()
        context['total_participants'] = sum(exam.participations.count() for exam in exams)
        context['courses'] = Course.objects.filter(teacher=teacher, is_active=True)
        
        return context


class TeacherExamsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """لیست امتحانات یک دوره"""
    template_name = 'teacher/teacher_exams.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = kwargs.get('course_id')
        
        try:
            teacher = Teacher.objects.get(user=self.request.user)
        except Teacher.DoesNotExist:
            return context
        
        from course.models import Exam
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        exams = Exam.objects.filter(course=course).order_by('-scheduled_start')
        
        context['course'] = course
        context['exams'] = exams
        context['final_exam'] = exams.filter(exam_type='final').first()
        context['midterm_exam'] = exams.filter(exam_type='midterm').first()
        context['quizzes'] = exams.filter(exam_type='quiz')
        
        return context


class TeacherCreateExamView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """ایجاد امتحان جدید"""
    template_name = 'teacher/teacher_exam_create.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = kwargs.get('course_id')
        
        try:
            teacher = Teacher.objects.get(user=self.request.user)
        except Teacher.DoesNotExist:
            return context
        
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        
        from course.forms import ExamForm
        if self.request.method == 'POST':
            form = ExamForm(self.request.POST, self.request.FILES, teacher=teacher, course=course)
        else:
            form = ExamForm(teacher=teacher, course=course)
        
        context['course'] = course
        context['form'] = form
        return context
    
    def post(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        
        try:
            teacher = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
            messages.error(request, 'شما مجاز به انجام این عملیات نیستید.')
            return redirect('dashboard:teacher_dashboard')
        
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        
        from course.forms import ExamForm
        form = ExamForm(request.POST, request.FILES, teacher=teacher, course=course)
        
        if form.is_valid():
            exam = form.save()
            messages.success(request, f'امتحان "{exam.title}" با موفقیت ایجاد شد.')
            return redirect('teacher:course_exams', course_id=course.id)
        else:
            messages.error(request, 'خطا در ایجاد امتحان. لطفاً اطلاعات را بررسی کنید.')
            return self.get(request, *args, **kwargs)


class TeacherEditExamView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """ویرایش امتحان"""
    template_name = 'teacher/teacher_exam_edit.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam_id = kwargs.get('exam_id')
        
        try:
            teacher = Teacher.objects.get(user=self.request.user)
        except Teacher.DoesNotExist:
            return context
        
        from course.models import Exam
        exam = get_object_or_404(Exam, id=exam_id, teacher=teacher)
        
        from course.forms import ExamForm
        if self.request.method == 'POST':
            form = ExamForm(self.request.POST, self.request.FILES, instance=exam, teacher=teacher, course=exam.course)
        else:
            form = ExamForm(instance=exam, teacher=teacher, course=exam.course)
        
        context['exam'] = exam
        context['course'] = exam.course
        context['form'] = form
        return context
    
    def post(self, request, *args, **kwargs):
        exam_id = kwargs.get('exam_id')
        
        try:
            teacher = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
            messages.error(request, 'شما مجاز به انجام این عملیات نیستید.')
            return redirect('dashboard:teacher_dashboard')
        
        from course.models import Exam
        exam = get_object_or_404(Exam, id=exam_id, teacher=teacher)
        
        from course.forms import ExamForm
        form = ExamForm(request.POST, request.FILES, instance=exam, teacher=teacher, course=exam.course)
        
        if form.is_valid():
            exam = form.save()
            messages.success(request, f'امتحان "{exam.title}" با موفقیت بروزرسانی شد.')
            return redirect('teacher:course_exams', course_id=exam.course.id)
        else:
            messages.error(request, 'خطا در بروزرسانی امتحان. لطفاً اطلاعات را بررسی کنید.')
            return self.get(request, *args, **kwargs)


class TeacherDeleteExamView(LoginRequiredMixin, UserPassesTestMixin, View):
    """حذف امتحان"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def post(self, request, exam_id):
        try:
            teacher = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
            messages.error(request, 'شما مجاز به انجام این عملیات نیستید.')
            return redirect('dashboard:teacher_dashboard')
        
        from course.models import Exam
        exam = get_object_or_404(Exam, id=exam_id, teacher=teacher)
        course_id = exam.course.id
        exam_title = exam.title
        
        exam.delete()
        messages.success(request, f'امتحان "{exam_title}" با موفقیت حذف شد.')
        return redirect('teacher:course_exams', course_id=course_id)


class TeacherExamParticipantsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """لیست شرکت‌کنندگان و نمره‌دهی"""
    template_name = 'teacher/teacher_exam_participants.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exam_id = kwargs.get('exam_id')
        
        try:
            teacher = Teacher.objects.get(user=self.request.user)
        except Teacher.DoesNotExist:
            return context
        
        from course.models import Exam, ExamParticipation
        exam = get_object_or_404(Exam, id=exam_id, teacher=teacher)
        participations = ExamParticipation.objects.filter(exam=exam).select_related('student__user').order_by('-started_at')
        
        context['exam'] = exam
        context['course'] = exam.course
        context['participations'] = participations
        context['total_participants'] = participations.count()
        context['submitted_count'] = participations.filter(status='submitted').count()
        context['graded_count'] = participations.filter(status='graded').count()
        
        return context


class TeacherGradeExamView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """نمره‌دهی یک شرکت‌کننده"""
    template_name = 'teacher/teacher_exam_grade.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participation_id = kwargs.get('participation_id')
        
        try:
            teacher = Teacher.objects.get(user=self.request.user)
        except Teacher.DoesNotExist:
            return context
        
        from course.models import ExamParticipation
        participation = get_object_or_404(ExamParticipation, id=participation_id, exam__teacher=teacher)
        
        context['participation'] = participation
        context['exam'] = participation.exam
        context['student'] = participation.student
        return context
    
    def post(self, request, *args, **kwargs):
        participation_id = kwargs.get('participation_id')
        
        try:
            teacher = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
            messages.error(request, 'شما مجاز به انجام این عملیات نیستید.')
            return redirect('dashboard:teacher_dashboard')
        
        from course.models import ExamParticipation
        participation = get_object_or_404(ExamParticipation, id=participation_id, exam__teacher=teacher)
        
        score = request.POST.get('score')
        feedback = request.POST.get('feedback', '')
        
        if score:
            try:
                participation.score = float(score)
                participation.feedback = feedback
                participation.status = 'graded'
                participation.graded_by = teacher
                participation.graded_at = timezone.now()
                participation.save()
                
                messages.success(request, f'نمره {participation.student.user.get_full_name()} با موفقیت ثبت شد.')
            except ValueError:
                messages.error(request, 'نمره وارد شده معتبر نیست.')
        
        return redirect('teacher:exam_participants', exam_id=participation.exam.id)
