from django.contrib.auth.views import TemplateView
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.shortcuts import render, get_object_or_404
from course.models import Course
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from account.models import Teacher
from course.forms import CourseForm
from course.models import Course
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
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
            from django.shortcuts import redirect
            return redirect('teacher:teacher_courses')
        return render(request, self.template_name, {'form': form, 'course': course})