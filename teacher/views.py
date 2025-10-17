from django.contrib.auth.views import TemplateView
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, FileResponse, Http404
from django.urls import reverse_lazy
from django.utils import timezone
from course.models import Course, Assignment, AssignmentSubmission, CourseResource, CourseVideo, Exam, ExamParticipation
from account.models import Teacher, Student
from course.forms import CourseForm, AssignmentForm
from enrollment.models import Enrollment
import os


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


class TeacherMyStudentsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """نمایش تمام زبان‌آموزان معلم در تمام دوره‌ها"""
    template_name = 'teacher/my_students.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            teacher = Teacher.objects.get(user=self.request.user)
        except Teacher.DoesNotExist:
            return context
        
        from enrollment.models import Enrollment
        
        # فیلترها
        course_filter = self.request.GET.get('course', '')
        search_query = self.request.GET.get('search', '')
        
        # دوره‌های معلم
        courses = Course.objects.filter(teacher=teacher, is_active=True)
        
        if course_filter:
            courses = courses.filter(id=course_filter)
        
        # زبان‌آموزان به تفکیک دوره
        students_by_course = []
        total_students = 0
        active_students = 0
        
        for course in courses:
            enrollments = Enrollment.objects.filter(course=course).select_related('student__user')
            
            if search_query:
                enrollments = enrollments.filter(
                    student__user__first_name__icontains=search_query
                ) | enrollments.filter(
                    student__user__last_name__icontains=search_query
                )
            
            if enrollments.exists():
                students_by_course.append({
                    'course': course,
                    'students': enrollments.order_by('-enrolled_at')
                })
                total_students += enrollments.count()
                active_students += enrollments.filter(status='confirmed').count()
        
        context['students_by_course'] = students_by_course
        context['total_students'] = total_students
        context['active_students'] = active_students
        context['courses'] = Course.objects.filter(teacher=teacher, is_active=True)
        context['courses_count'] = courses.count()
        
        return context


class TeacherCourseStudentView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teacher/teacher_course_students.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = kwargs.get('course_id')
        
        try:
            teacher = Teacher.objects.get(user=self.request.user)
        except Teacher.DoesNotExist:
            return context
        
        from enrollment.models import Enrollment
        
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        enrollments = Enrollment.objects.filter(course=course).select_related('student__user').order_by('-enrolled_at')
        
        # آمار
        confirmed_count = enrollments.filter(status='confirmed').count()
        pending_count = enrollments.filter(status='pending').count()
        remaining_capacity = course.capacity - enrollments.filter(status='confirmed').count()
        
        context['course'] = course
        context['enrollments'] = enrollments
        context['confirmed_count'] = confirmed_count
        context['pending_count'] = pending_count
        context['remaining_capacity'] = remaining_capacity if remaining_capacity > 0 else 0
        
        return context

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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from core.models import ContactMessage
        from datetime import date
        
        user = self.request.user
        today = date.today()
        
        # پیام‌های ارسال شده به پشتیبانی (از معلم به ادمین)
        admin_messages = ContactMessage.objects.filter(
            email=user.email,
            subject__startswith='[معلم]'
        ).order_by('-created_at')
        
        # تعداد پیام‌های ارسال شده امروز
        messages_today = ContactMessage.objects.filter(
            email=user.email,
            subject__startswith='[معلم]',
            created_at__date=today
        ).count()
        
        # تعداد پیام‌های باقی‌مانده
        remaining_messages = max(0, 3 - messages_today)
        
        # تعداد پیام‌های خوانده نشده از ادمین
        unread_admin_messages = admin_messages.filter(status='replied', reply__isnull=False).exclude(reply='').count()
        
        # پیام‌های زبان‌آموزان
        from core.models import StudentTeacherMessage
        try:
            teacher = Teacher.objects.get(user=user)
            student_messages = StudentTeacherMessage.objects.filter(
                teacher=teacher
            ).select_related('student__user', 'course').order_by('-created_at')
            unread_student_messages = student_messages.filter(is_read=False).count()
        except Teacher.DoesNotExist:
            student_messages = []
            unread_student_messages = 0
        
        context['admin_messages'] = admin_messages
        context['student_messages'] = student_messages
        context['remaining_messages'] = remaining_messages
        context['messages_today'] = messages_today
        context['unread_admin_messages'] = unread_admin_messages
        context['unread_student_messages'] = unread_student_messages
        
        return context


@login_required
def teacher_send_message(request):
    """ارسال پیام به پشتیبانی با محدودیت روزانه"""
    if request.method != 'POST':
        return redirect('teacher:messages')
    
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'teacher':
        messages.error(request, 'دسترسی غیرمجاز.')
        return redirect('core:home')
    
    from core.models import ContactMessage
    from datetime import date
    
    today = date.today()
    
    # بررسی محدودیت روزانه
    messages_today = ContactMessage.objects.filter(
        email=request.user.email,
        created_at__date=today
    ).count()
    
    if messages_today >= 3:
        messages.error(request, 'شما امروز سقف مجاز ارسال پیام (3 پیام) را استفاده کرده‌اید.')
        return redirect('teacher:messages')
    
    # ایجاد پیام
    subject = request.POST.get('subject', '')
    message_text = request.POST.get('message', '')
    
    if not subject or not message_text:
        messages.error(request, 'لطفاً تمام فیلدها را پر کنید.')
        return redirect('teacher:messages')
    
    # دریافت شماره تلفن معلم
    try:
        teacher = Teacher.objects.get(user=request.user)
        phone = teacher.phone_number if teacher.phone_number else ''
    except Teacher.DoesNotExist:
        phone = ''
    
    ContactMessage.objects.create(
        name=request.user.get_full_name(),
        email=request.user.email,
        phone=phone,
        subject=f'[معلم] {subject}',
        message=message_text,
        status='new'
    )
    
    messages.success(request, 'پیام شما با موفقیت ارسال شد. پشتیبانی به زودی پاسخ خواهد داد.')
    return redirect('teacher:messages')


@login_required
def teacher_reply_student_message(request, message_id):
    """پاسخ معلم به پیام زبان‌آموز"""
    if request.method != 'POST':
        return redirect('teacher:messages')
    
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'teacher':
        messages.error(request, 'دسترسی غیرمجاز.')
        return redirect('core:home')
    
    from core.models import StudentTeacherMessage
    from django.utils import timezone
    
    try:
        teacher = Teacher.objects.get(user=request.user)
        msg = get_object_or_404(StudentTeacherMessage, id=message_id, teacher=teacher)
        
        reply_text = request.POST.get('reply', '')
        
        if not reply_text:
            messages.error(request, 'لطفاً متن پاسخ را وارد کنید.')
            return redirect('teacher:messages')
        
        msg.teacher_reply = reply_text
        msg.replied_at = timezone.now()
        msg.is_read = True
        msg.save()
        
        messages.success(request, 'پاسخ شما با موفقیت ارسال شد.')
    except Teacher.DoesNotExist:
        messages.error(request, 'حساب معلم یافت نشد.')
    
    return redirect('teacher:messages')


@login_required
def teacher_mark_message_read(request, message_id):
    """علامت‌گذاری پیام به عنوان خوانده شده"""
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'teacher':
        messages.error(request, 'دسترسی غیرمجاز.')
        return redirect('core:home')
    
    from core.models import StudentTeacherMessage
    
    try:
        teacher = Teacher.objects.get(user=request.user)
        msg = get_object_or_404(StudentTeacherMessage, id=message_id, teacher=teacher)
        
        msg.is_read = True
        msg.save()
        
        messages.success(request, 'پیام به عنوان خوانده شده علامت‌گذاری شد.')
    except Teacher.DoesNotExist:
        messages.error(request, 'حساب معلم یافت نشد.')
    
    return redirect('teacher:messages')


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
class TeacherEditCourseView(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = 'teacher/teacher_edit_course.html'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'

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
            updated_course = form.save()
            messages.success(request, f'دوره "{updated_course.title}" با موفقیت ویرایش شد.')
            return redirect('teacher:teacher_courses')
        else:
            # نمایش خطاها در console/log
            print("Form errors:", form.errors)
            messages.error(request, 'لطفاً خطاهای فرم را بررسی و تصحیح کنید.')
        return render(request, self.template_name, {'form': form, 'course': course})


# Assignment Views
@method_decorator(login_required, name='dispatch')
class TeacherAssignmentsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """نمایش لیست تکالیف معلم"""
    template_name = 'teacher/teacher_assignments.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = kwargs.get('course_id')
        
        try:
            teacher = Teacher.objects.get(user=self.request.user)
        except Teacher.DoesNotExist:
            return context
        
        from course.models import AssignmentSubmission
        
        # فیلترها
        course_filter = self.request.GET.get('course', '')
        status_filter = self.request.GET.get('status', '')
        
        if course_id:
            # نمایش تکالیف یک دوره خاص
            course = get_object_or_404(Course, id=course_id, teacher=teacher)
            assignments = Assignment.objects.filter(course=course, teacher=teacher).order_by('-created_at')
            context['course'] = course
            context['single_course'] = True
        else:
            # نمایش همه تکالیف معلم
            assignments = Assignment.objects.filter(teacher=teacher).select_related('course').order_by('-created_at')
            
            if course_filter:
                assignments = assignments.filter(course_id=course_filter)
            
            context['single_course'] = False
        
        # اضافه کردن تعداد submissions برای هر تکلیف
        for assignment in assignments:
            assignment.graded_count = AssignmentSubmission.objects.filter(
                assignment=assignment,
                graded_by__isnull=False
            ).count()
        
        # آمار
        all_submissions = AssignmentSubmission.objects.filter(assignment__teacher=teacher)
        
        if status_filter == 'pending':
            # فقط تکالیف با ارسالی‌های در انتظار
            assignments = [a for a in assignments if all_submissions.filter(assignment=a, graded_by__isnull=True).exists()]
        elif status_filter == 'graded':
            assignments = [a for a in assignments if all_submissions.filter(assignment=a, graded_by__isnull=False).exists()]
        
        context['assignments'] = assignments
        context['courses'] = Course.objects.filter(teacher=teacher, is_active=True)
        context['total_assignments'] = Assignment.objects.filter(teacher=teacher).count()
        context['pending_submissions'] = all_submissions.filter(graded_by__isnull=True).count()
        context['graded_submissions'] = all_submissions.filter(graded_by__isnull=False).count()
        context['total_submissions'] = all_submissions.count()
        
        # تکالیف در انتظار بررسی (برای جدول جداگانه)
        context['pending_assignments_list'] = all_submissions.filter(
            graded_by__isnull=True
        ).select_related('student__user', 'assignment__course').order_by('-submitted_at')[:10]
        
        return context


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
            today = timezone.now()
            week_later = today + timezone.timedelta(days=7)
            upcoming_exams = Exam.objects.filter(
                course__teacher=teacher,
                scheduled_start__gte=today,
                scheduled_start__lte=week_later
            ).select_related('course').order_by('scheduled_start')[:5]
            
            for exam in upcoming_exams:
                notifications.append({
                    'title': 'امتحان پیش رو',
                    'message': f'امتحان "{exam.title}" دوره "{exam.course.title}" در {exam.scheduled_start.strftime("%Y-%m-%d")}',
                    'created_at': timezone.now(),
                    'type': 'warning',
                    'is_read': False,
                    'action_url': f'/teachers/exams/{exam.id}/participants/',
                })
        
        # اعلان‌های کلاس پیش رو
        if filter_type in ['all']:
            today = timezone.now().date()
            week_end = today + timezone.timedelta(days=7)
            upcoming_courses = Course.objects.filter(
                teacher=teacher,
                is_active=True,
                start_date__lte=week_end,
                end_date__gte=today
            ).order_by('start_date')[:5]
            
            for course in upcoming_courses:
                notifications.append({
                    'title': 'کلاس پیش رو',
                    'message': f'دوره "{course.title}" - {course.enrolled_count} دانش‌آموز ثبت‌نام کرده',
                    'created_at': timezone.now(),
                    'type': 'info',
                    'is_read': False,
                    'action_url': f'/teachers/courses/{course.id}/students/',
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
        
        exams = Exam.objects.filter(course__teacher=teacher).select_related('course').order_by('-scheduled_start')
        
        if course_filter:
            exams = exams.filter(course_id=course_filter)
        
        if type_filter:
            exams = exams.filter(exam_type=type_filter)
        
        today = timezone.now()
        if status_filter == 'upcoming':
            exams = exams.filter(scheduled_start__gt=today)
        elif status_filter == 'ongoing':
            exams = exams.filter(scheduled_start__lte=today, scheduled_end__gte=today)
        elif status_filter == 'completed':
            exams = exams.filter(scheduled_end__lt=today)
        
        # آمار
        context['exams'] = exams
        context['total_exams'] = exams.count()
        context['upcoming_exams'] = exams.filter(scheduled_start__gt=today).count()
        context['completed_exams'] = exams.filter(scheduled_end__lt=today).count()
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


# ============================
# Course Videos Management
# ============================

class TeacherCourseVideosView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """نمایش لیست ویدیوهای دوره"""
    template_name = 'teacher/teacher_course_videos.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = kwargs.get('course_id')
        
        teacher = get_object_or_404(Teacher, user=self.request.user)
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        videos = CourseVideo.objects.filter(course=course).order_by('order', '-created_at')
        
        context['course'] = course
        context['videos'] = videos
        return context


class TeacherCreateVideoView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """ایجاد ویدیوی جدید برای دوره"""
    model = CourseVideo
    fields = ['title', 'description', 'video_file', 'video_url', 'duration', 'order', 'is_free_preview', 'is_active']
    template_name = 'teacher/teacher_video_form.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def dispatch(self, request, *args, **kwargs):
        teacher = get_object_or_404(Teacher, user=request.user)
        self.course = get_object_or_404(Course, id=kwargs['course_id'], teacher=teacher)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        context['form_title'] = 'افزودن ویدیوی آموزشی'
        return context
    
    def form_valid(self, form):
        form.instance.course = self.course
        messages.success(self.request, 'ویدیو با موفقیت اضافه شد.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('teacher:course_videos', kwargs={'course_id': self.course.id})


class TeacherEditVideoView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """ویرایش ویدیوی آموزشی"""
    model = CourseVideo
    fields = ['title', 'description', 'video_file', 'video_url', 'duration', 'order', 'is_free_preview', 'is_active']
    template_name = 'teacher/teacher_video_form.html'
    pk_url_kwarg = 'video_id'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_queryset(self):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        return CourseVideo.objects.filter(course__teacher=teacher)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.object.course
        context['form_title'] = 'ویرایش ویدیوی آموزشی'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'ویدیو با موفقیت ویرایش شد.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('teacher:course_videos', kwargs={'course_id': self.object.course.id})


class TeacherDeleteVideoView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """حذف ویدیوی آموزشی"""
    model = CourseVideo
    pk_url_kwarg = 'video_id'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_queryset(self):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        return CourseVideo.objects.filter(course__teacher=teacher)
    
    def get_success_url(self):
        messages.success(self.request, 'ویدیو با موفقیت حذف شد.')
        return reverse_lazy('teacher:course_videos', kwargs={'course_id': self.object.course.id})


# ============================
# Course Resources Management
# ============================

class TeacherCourseResourcesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """نمایش لیست منابع دوره"""
    template_name = 'teacher/teacher_course_resources.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = kwargs.get('course_id')
        
        teacher = get_object_or_404(Teacher, user=self.request.user)
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        resources = CourseResource.objects.filter(course=course).order_by('order', '-created_at')
        
        context['course'] = course
        context['resources'] = resources
        return context


class TeacherCreateResourceView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """ایجاد منبع جدید برای دوره"""
    model = CourseResource
    fields = ['title', 'description', 'resource_type', 'file', 'link', 'order', 'is_active']
    template_name = 'teacher/teacher_resource_form.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def dispatch(self, request, *args, **kwargs):
        teacher = get_object_or_404(Teacher, user=request.user)
        self.course = get_object_or_404(Course, id=kwargs['course_id'], teacher=teacher)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        context['form_title'] = 'افزودن منبع آموزشی'
        return context
    
    def form_valid(self, form):
        form.instance.course = self.course
        messages.success(self.request, 'منبع با موفقیت اضافه شد.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('teacher:course_resources', kwargs={'course_id': self.course.id})


class TeacherEditResourceView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """ویرایش منبع آموزشی"""
    model = CourseResource
    fields = ['title', 'description', 'resource_type', 'file', 'link', 'order', 'is_active']
    template_name = 'teacher/teacher_resource_form.html'
    pk_url_kwarg = 'resource_id'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_queryset(self):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        return CourseResource.objects.filter(course__teacher=teacher)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.object.course
        context['form_title'] = 'ویرایش منبع آموزشی'
        return context
    
    def form_valid(self, form):
        messages.success(self.request, 'منبع با موفقیت ویرایش شد.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('teacher:course_resources', kwargs={'course_id': self.object.course.id})


class TeacherDeleteResourceView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """حذف منبع آموزشی"""
    model = CourseResource
    pk_url_kwarg = 'resource_id'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_queryset(self):
        teacher = get_object_or_404(Teacher, user=self.request.user)
        return CourseResource.objects.filter(course__teacher=teacher)
    
    def get_success_url(self):
        messages.success(self.request, 'منبع با موفقیت حذف شد.')
        return reverse_lazy('teacher:course_resources', kwargs={'course_id': self.object.course.id})


# ============================
# Course Grades View
# ============================

class TeacherCourseGradesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """نمایش نمرات دانش‌آموزان یک دوره خاص"""
    template_name = 'teacher/teacher_course_grades.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course_id = kwargs.get('course_id')
        
        teacher = get_object_or_404(Teacher, user=self.request.user)
        course = get_object_or_404(Course, id=course_id, teacher=teacher)
        
        # دریافت دانش‌آموزان دوره
        enrollments = Enrollment.objects.filter(
            course=course,
            status='confirmed'
        ).select_related('student__user').order_by('student__user__first_name')
        
        # دریافت امتحانات دوره
        exams = Exam.objects.filter(course=course).order_by('scheduled_start')
        
        # دریافت تکالیف دوره
        assignments = Assignment.objects.filter(course=course, is_active=True).order_by('due_date')
        
        # ساختن جدول نمرات
        grades_data = []
        for enrollment in enrollments:
            student = enrollment.student
            student_data = {
                'student': student,
                'enrollment': enrollment,
                'exam_grades': {},
                'assignment_grades': {},
                'total_exam_score': 0,
                'total_assignment_score': 0,
                'exam_average': 0,
                'assignment_average': 0,
                'overall_average': 0,
            }
            
            # نمرات امتحانات
            exam_total_points = 0
            exam_earned_points = 0
            for exam in exams:
                participation = ExamParticipation.objects.filter(
                    exam=exam,
                    student=student,
                    status='graded'
                ).first()
                
                if participation and participation.score is not None:
                    student_data['exam_grades'][exam.id] = {
                        'score': participation.score,
                        'total': exam.total_points,
                        'percentage': (participation.score / exam.total_points * 100) if exam.total_points else 0
                    }
                    exam_earned_points += participation.score
                    exam_total_points += exam.total_points
                else:
                    student_data['exam_grades'][exam.id] = None
            
            if exam_total_points > 0:
                student_data['exam_average'] = (exam_earned_points / exam_total_points * 100)
            
            # نمرات تکالیف
            assignment_total_points = 0
            assignment_earned_points = 0
            for assignment in assignments:
                submission = AssignmentSubmission.objects.filter(
                    assignment=assignment,
                    student=student,
                    status='graded'
                ).first()
                
                if submission and submission.score is not None:
                    student_data['assignment_grades'][assignment.id] = {
                        'score': submission.score,
                        'total': assignment.total_points,
                        'percentage': (submission.score / assignment.total_points * 100) if assignment.total_points else 0
                    }
                    assignment_earned_points += submission.score
                    assignment_total_points += assignment.total_points
                else:
                    student_data['assignment_grades'][assignment.id] = None
            
            if assignment_total_points > 0:
                student_data['assignment_average'] = (assignment_earned_points / assignment_total_points * 100)
            
            # میانگین کلی (50% امتحانات + 50% تکالیف)
            if student_data['exam_average'] > 0 or student_data['assignment_average'] > 0:
                student_data['overall_average'] = (student_data['exam_average'] * 0.5) + (student_data['assignment_average'] * 0.5)
            
            grades_data.append(student_data)
        
        context['course'] = course
        context['enrollments'] = enrollments
        context['exams'] = exams
        context['assignments'] = assignments
        context['grades_data'] = grades_data
        
        return context


# ============================
# Certificate Management
# ============================

class TeacherUploadCertificateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """آپلود مدرک برای دانش‌آموز"""
    template_name = 'teacher/teacher_upload_certificate.html'
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.user_type == 'teacher'
    
    def get(self, request, enrollment_id):
        teacher = get_object_or_404(Teacher, user=request.user)
        enrollment = get_object_or_404(
            Enrollment, 
            id=enrollment_id, 
            course__teacher=teacher
        )
        
        context = {
            'enrollment': enrollment,
            'student': enrollment.student,
            'course': enrollment.course,
            'can_upload': enrollment.can_upload_certificate,
            'has_final_grade': enrollment.has_final_grade,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, enrollment_id):
        teacher = get_object_or_404(Teacher, user=request.user)
        enrollment = get_object_or_404(
            Enrollment, 
            id=enrollment_id, 
            course__teacher=teacher
        )
        
        # بررسی امکان آپلود مدرک
        if not enrollment.can_upload_certificate:
            messages.error(request, 'امکان آپلود مدرک وجود ندارد. ابتدا باید نمره نهایی وارد شود.')
            return redirect('teacher:upload_certificate', enrollment_id=enrollment_id)
        
        # دریافت فایل
        certificate_file = request.FILES.get('certificate')
        
        if not certificate_file:
            messages.error(request, 'لطفاً فایل مدرک را انتخاب کنید.')
            return redirect('teacher:upload_certificate', enrollment_id=enrollment_id)
        
        # بررسی فرمت فایل
        if not certificate_file.name.endswith('.pdf'):
            messages.error(request, 'فقط فایل‌های PDF مجاز هستند.')
            return redirect('teacher:upload_certificate', enrollment_id=enrollment_id)
        
        # حذف مدرک قبلی اگر وجود دارد
        if enrollment.certificate:
            if os.path.isfile(enrollment.certificate.path):
                os.remove(enrollment.certificate.path)
        
        # ذخیره مدرک جدید
        enrollment.certificate = certificate_file
        enrollment.certificate_uploaded_at = timezone.now()
        enrollment.save()
        
        messages.success(
            request, 
            f'مدرک {enrollment.student.user.get_full_name()} با موفقیت آپلود شد.'
        )
        return redirect('teacher:course_grades', course_id=enrollment.course.id)


@login_required
def teacher_delete_certificate(request, enrollment_id):
    """حذف مدرک دانش‌آموز"""
    if request.method != 'POST':
        return redirect('teacher:teacher_courses')
    
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'teacher':
        messages.error(request, 'دسترسی غیرمجاز.')
        return redirect('core:home')
    
    teacher = get_object_or_404(Teacher, user=request.user)
    enrollment = get_object_or_404(
        Enrollment, 
        id=enrollment_id, 
        course__teacher=teacher
    )
    
    if enrollment.certificate:
        # حذف فایل از سیستم
        if os.path.isfile(enrollment.certificate.path):
            os.remove(enrollment.certificate.path)
        
        # حذف از دیتابیس
        enrollment.certificate = None
        enrollment.certificate_uploaded_at = None
        enrollment.save()
        
        messages.success(request, 'مدرک با موفقیت حذف شد.')
    else:
        messages.warning(request, 'مدرکی برای حذف وجود ندارد.')
    
    return redirect('teacher:course_grades', course_id=enrollment.course.id)
