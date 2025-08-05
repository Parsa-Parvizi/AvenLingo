from django.contrib.auth.views import TemplateView
from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.shortcuts import render, get_object_or_404
from course.models import Course
from django.views.generic import ListView, DetailView
from .models import Teacher
from course.forms import CourseForm
from course.models import Course
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages

class TeacherDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'teacher_dashboard.html'

    def test_func(self):
        return self.request.user.groups.filter(name='Teachers').exists()


class TeacherCourseView(LoginRequiredMixin, View):
    def get(self, request):
        teacher = request.user
        courses = Course.objects.filter(teacher=teacher) # type: ignore
        return render(request, 'teacher_courses.html', {'courses': courses})


class TeacherCourseStudentView(LoginRequiredMixin, View):
    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id, teacher=request.user)
        students = course.students.all()  # فرض بر اینکه یک related name داری
        return render(request, 'teacher_course_students.html', {'course': course, 'students': students})

class AllTeacherView(ListView):
    model = Teacher
    template_name = 'teacher_list.html'
    context_object_name = 'teachers'
    paginate_by = 10


class TeacherDetailView(DetailView):
    model = Teacher
    template_name = 'teacher_detail.html'
    context_object_name = 'teacher'
    pk_url_kwarg = 'teacher_id'

@method_decorator(login_required, name='dispatch')
class TeacherCreateCourseView(View):
    template_name = 'teacher_create_course.html'

    def get(self, request):
        form = CourseForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user.teacher_profile
            course.status = 'pending'
            course.save()
            messages.success(request, 'کلاس شما با موفقیت ثبت شد و پس از تایید ادمین منتشر خواهد شد.')
            return render(request, self.template_name, {'form': CourseForm()})
        return render(request, self.template_name, {'form': form})