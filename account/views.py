from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, TemplateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.utils import timezone
import secrets

from .models import User, Student, Teacher, TeacherApplication
from .forms import (
    StudentRegistrationForm, TeacherRegistrationForm, CustomLoginForm,
    TeacherApplicationForm, StudentProfileForm, TeacherProfileForm
)


class StudentRegistrationView(CreateView):
    """Registration view for students"""
    model = User
    form_class = StudentRegistrationForm
    template_name = 'account/student_register.html'
    success_url = reverse_lazy('account:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f'حساب کاربری شما با موفقیت ایجاد شد. لطفاً وارد شوید.'
        )
        return response
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('account:dashboard')
        return super().dispatch(request, *args, **kwargs)


class TeacherRegistrationView(CreateView):
    """Registration view for teachers (only for accepted applications)"""
    model = User
    form_class = TeacherRegistrationForm
    template_name = 'account/teacher_register.html'
    success_url = reverse_lazy('account:login')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('account:dashboard')
        
        # Get email from URL parameter
        email = self.kwargs.get('email')
        if not email:
            messages.error(request, 'ایمیل معتبر نیست.')
            return redirect('account:teacher_apply')
        
        # Check if there's an accepted application for this email
        try:
            application = TeacherApplication.objects.get(email=email, status='accepted')
            # Check if teacher account doesn't already exist
            if Teacher.objects.filter(application=application).exists():
                messages.error(request, 'حساب کاربری برای این درخواست قبلاً ایجاد شده است.')
                return redirect('account:login')
            self.application = application
        except TeacherApplication.DoesNotExist:
            messages.error(request, 'درخواست تایید شده‌ای برای این ایمیل یافت نشد.')
            return redirect('account:teacher_apply')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['application'] = self.application
        return kwargs
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            'حساب کاربری مدرس شما با موفقیت ایجاد شد. لطفاً وارد شوید.'
        )
        return response


class CustomLoginView(LoginView):
    """Custom login view using email"""
    form_class = CustomLoginForm
    template_name = 'account/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('account:dashboard')
    
    def form_valid(self, form):
        messages.success(self.request, f'خوش آمدید، {form.get_user().get_full_name()}!')
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    """Custom logout view"""
    next_page = reverse_lazy('core:home')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(request, 'شما با موفقیت خارج شدید.')
        return super().dispatch(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, TemplateView):
    """Universal dashboard that redirects to appropriate user dashboard"""
    
    def get(self, request, *args, **kwargs):
        user = request.user
        
        if user.user_type == 'student':
            return redirect('account:student_dashboard')
        elif user.user_type == 'teacher':
            return redirect('account:teacher_dashboard')
        elif user.user_type == 'admin':
            return redirect('admin:index')
        else:
            messages.error(request, 'نوع کاربری نامعتبر است.')
            return redirect('account:login')


class StudentDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Dashboard for students"""
    template_name = 'account/student_dashboard.html'
    
    def test_func(self):
        return self.request.user.user_type == 'student'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = get_object_or_404(Student, user=self.request.user)
        context['student'] = student
        
        # Get student's enrolled courses (if course app is implemented)
        # context['enrolled_courses'] = student.enrollments.filter(is_active=True)
        
        return context


class TeacherDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Dashboard for teachers"""
    template_name = 'account/teacher_dashboard.html'
    
    def test_func(self):
        return self.request.user.user_type == 'teacher'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = get_object_or_404(Teacher, user=self.request.user)
        context['teacher'] = teacher
        
        # Get teacher's courses and students (if course app is implemented)
        # context['courses'] = teacher.courses.filter(is_active=True)
        # context['total_students'] = sum(course.enrollments.count() for course in context['courses'])
        
        return context


class TeacherApplicationView(CreateView):
    """View for teacher application submission"""
    model = TeacherApplication
    form_class = TeacherApplicationForm
    template_name = 'account/teacher_apply.html'
    success_url = reverse_lazy('account:teacher_apply_success')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            'درخواست همکاری شما با موفقیت ارسال شد. پس از بررسی، نتیجه از طریق ایمیل اطلاع داده خواهد شد.'
        )
        return response


class TeacherApplicationSuccessView(TemplateView):
    """Success page after teacher application submission"""
    template_name = 'account/teacher_apply_success.html'


class StudentProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Student profile edit view"""
    model = Student
    form_class = StudentProfileForm
    template_name = 'account/student_profile.html'
    success_url = reverse_lazy('account:student_dashboard')
    
    def test_func(self):
        return self.request.user.user_type == 'student'
    
    def get_object(self):
        return get_object_or_404(Student, user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'پروفایل شما با موفقیت بروزرسانی شد.')
        return super().form_valid(form)


class TeacherProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Teacher profile edit view"""
    model = Teacher
    form_class = TeacherProfileForm
    template_name = 'account/teacher_profile.html'
    success_url = reverse_lazy('account:teacher_dashboard')
    
    def test_func(self):
        return self.request.user.user_type == 'teacher'
    
    def get_object(self):
        return get_object_or_404(Teacher, user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'پروفایل شما با موفقیت بروزرسانی شد.')
        return super().form_valid(form)


# Admin views for managing teacher applications
class TeacherApplicationListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Admin view to list teacher applications"""
    template_name = 'account/admin/teacher_applications.html'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.user_type == 'admin'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pending_applications'] = TeacherApplication.objects.filter(status='pending').order_by('-submitted_at')
        context['accepted_applications'] = TeacherApplication.objects.filter(status='accepted').order_by('-reviewed_at')
        context['rejected_applications'] = TeacherApplication.objects.filter(status='rejected').order_by('-reviewed_at')
        return context


class TeacherApplicationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Admin view to view teacher application details"""
    model = TeacherApplication
    template_name = 'account/admin/teacher_application_detail.html'
    context_object_name = 'application'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.user_type == 'admin'


@method_decorator(login_required, name='dispatch')
class TeacherApplicationApprovalView(UserPassesTestMixin, TemplateView):
    """Admin view to approve/reject teacher applications"""
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.user_type == 'admin'
    
    def post(self, request, pk):
        application = get_object_or_404(TeacherApplication, pk=pk)
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        if action == 'accept':
            application.mark_as_accepted(request.user)
            messages.success(request, f'درخواست {application.first_name} {application.last_name} پذیرفته شد.')
            
            # Send email to teacher (you can implement email sending here)
            # application.email_user(
            #     'درخواست همکاری شما پذیرفته شد',
            #     f'سلام {application.first_name}، درخواست همکاری شما پذیرفته شد. می‌توانید با لینک زیر حساب کاربری ایجاد کنید.'
            # )
            
        elif action == 'reject':
            application.mark_as_rejected(request.user, admin_notes)
            messages.success(request, f'درخواست {application.first_name} {application.last_name} رد شد.')
        
        return redirect('account:admin_teacher_applications')


# Public view for checking teacher registration eligibility
def check_teacher_registration(request, email):
    """Check if a teacher can register with given email"""
    try:
        application = TeacherApplication.objects.get(email=email, status='accepted')
        # Check if teacher account doesn't already exist
        if Teacher.objects.filter(application=application).exists():
            messages.error(request, 'حساب کاربری برای این ایمیل قبلاً ایجاد شده است.')
            return redirect('account:login')
        return redirect('account:teacher_register', email=email)
    except TeacherApplication.DoesNotExist:
        messages.error(request, 'درخواست تایید شده‌ای برای این ایمیل یافت نشد.')
        return redirect('account:teacher_apply')

