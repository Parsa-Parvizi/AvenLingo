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
    """Enhanced registration view for students with security features"""
    model = User
    form_class = StudentRegistrationForm
    template_name = 'account/student_register.html'
    success_url = reverse_lazy('account:login')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        # Additional security check
        if not self.check_security():
            messages.error(self.request, 'خطای امنیتی تشخیص داده شد.')
            return self.form_invalid(form)
            
        response = super().form_valid(form)
        
        # Enhanced success message with user's name
        user_name = form.cleaned_data.get('first_name', 'کاربر')
        messages.success(
            self.request,
            f'{user_name} عزیز، حساب کاربری شما با موفقیت ایجاد شد. لطفاً وارد شوید.'
        )
        
        # Log successful registration
        import logging
        logger = logging.getLogger('account.registration')
        logger.info(f'Student registered successfully: {form.cleaned_data["email"]}')
        
        return response
    
    def form_invalid(self, form):
        # Log invalid form submission
        import logging
        logger = logging.getLogger('account.registration')
        logger.warning(f'Invalid registration attempt from IP: {self.get_client_ip()}')
        
        return super().form_invalid(form)
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('account:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def check_security(self):
        """Additional security checks"""
        # Check for rapid successive requests
        ip = self.get_client_ip()
        cache_key = f'rapid_registration_{ip}'
        
        from django.core.cache import cache
        if cache.get(cache_key):
            return False
            
        cache.set(cache_key, True, 60)  # 1 minute cooldown
        return True
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


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
    """Enhanced login view with security features"""
    form_class = CustomLoginForm
    template_name = 'account/login.html'
    redirect_authenticated_user = True
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def get_success_url(self):
        # Redirect based on user type
        user = self.request.user
        if user.user_type == 'student':
            return reverse_lazy('account:student_dashboard')
        elif user.user_type == 'teacher':
            return reverse_lazy('account:teacher_dashboard')
        elif user.user_type == 'admin':
            return reverse_lazy('admin:index')
        return reverse_lazy('account:dashboard')
    
    def form_valid(self, form):
        # Enhanced security logging
        user = form.get_user()
        import logging
        logger = logging.getLogger('account.login')
        logger.info(f'Successful login: {user.email} ({user.user_type}) from IP: {self.get_client_ip()}')
        
        # Set session timeout based on remember_me
        remember_me = form.cleaned_data.get('remember_me', False)
        if remember_me:
            self.request.session.set_expiry(1209600)  # 2 weeks
        else:
            self.request.session.set_expiry(3600)  # 1 hour
        
        # Welcome message based on user type and time
        from datetime import datetime
        hour = datetime.now().hour
        
        if hour < 12:
            greeting = 'صبح بخیر'
        elif hour < 18:
            greeting = 'ظهر بخیر'
        else:
            greeting = 'عصر بخیر'
        
        user_name = user.get_full_name() or user.first_name
        if user.user_type == 'student':
            message = f'{greeting} {user_name}! به داشبورد آموزشی خود خوش آمدید.'
        elif user.user_type == 'teacher':
            message = f'{greeting} استاد {user_name}! آماده تدریس هستید؟'
        else:
            message = f'{greeting} {user_name}!'
            
        messages.success(self.request, message)
        
        # Update last login activity
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # Enhanced error handling
        import logging
        logger = logging.getLogger('account.login')
        
        # Check if it's a rate limit error
        if 'rate_limited' in str(form.errors):
            messages.error(self.request, 
                'به دلیل تلاش‌های مکرر ناموفق، دسترسی شما موقتاً محدود شده است. لطفاً ۱۵ دقیقه بعد تلاش کنید.')
        else:
            messages.error(self.request, 
                'ایمیل یا رمز عبور اشتباه است. لطفاً دوباره تلاش کنید.')
        
        logger.warning(f'Failed login attempt from IP: {self.get_client_ip()}')
        return super().form_invalid(form)
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class CustomLogoutView(LogoutView):
    """Custom logout view with enhanced security and UX"""
    next_page = reverse_lazy('core:home')
    template_name = 'account/logout_confirm.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Store user info before logout for personalized message
        if request.user.is_authenticated:
            self.user_name = request.user.get_full_name() or request.user.first_name
            self.user_type = request.user.user_type
            
            # Security: Log logout action for audit trail
            import logging
            logger = logging.getLogger('account.logout')
            logger.info(f'User logout: {request.user.email} ({request.user.user_type}) from IP: {self.get_client_ip(request)}')
            
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Handle POST logout with enhanced security"""
        if request.user.is_authenticated:
            user_name = request.user.get_full_name() or request.user.first_name
            user_type = request.user.user_type
            
            # Clear specific session data
            if hasattr(request.session, 'cycle_key'):
                request.session.cycle_key()  # Generate new session key for security
            
            # Custom logout message based on user type
            if user_type == 'student':
                message = f'خداحافظ {user_name}! امیدواریم به زودی برای ادامه یادگیری برگردید.'
            elif user_type == 'teacher':
                message = f'استاد {user_name}، با تشکر از حضورتان. موفق باشید!'
            else:
                message = f'{user_name} عزیز، با موفقیت خارج شدید.'
                
            messages.success(request, message)
            
        response = super().post(request, *args, **kwargs)
        
        # Enhanced security: Clear sensitive cookies
        if response:
            response.delete_cookie('sessionid')
            response.delete_cookie('csrftoken')
            
        return response
    
    def get(self, request, *args, **kwargs):
        """Handle GET request for logout confirmation"""
        if not request.user.is_authenticated:
            messages.info(request, 'شما قبلاً خارج شده‌اید.')
            return redirect('core:home')
        
        # For AJAX requests, direct logout
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return self.post(request, *args, **kwargs)
            
        return super().get(request, *args, **kwargs)
    
    def get_client_ip(self, request):
        """Get client IP address for logging"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['user_name'] = self.request.user.get_full_name() or self.request.user.first_name
            context['user_type'] = self.request.user.user_type
            context['user_type_display'] = self.request.user.get_user_type_display()
        return context


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
        
        # Import here to avoid circular imports
        from enrollment.models import Enrollment
        from course.models import Course
        
        # Get student's enrollments with course details
        enrollments = Enrollment.objects.filter(student=student).select_related('course', 'course__teacher', 'course__category').order_by('-enrolled_at')
        context['enrollments'] = enrollments
        context['total_enrollments'] = enrollments.count()
        context['confirmed_enrollments'] = enrollments.filter(status='confirmed').count()
        context['pending_enrollments'] = enrollments.filter(status='pending').count()
        context['cancelled_enrollments'] = enrollments.filter(status='cancelled').count()
        context['completed_enrollments'] = enrollments.filter(status='completed').count()
        
        # Payment statistics
        context['paid_enrollments'] = enrollments.filter(payment_status='paid').count()
        context['unpaid_enrollments'] = enrollments.filter(payment_status='unpaid').count()
        context['overdue_payments'] = enrollments.filter(
            payment_status='unpaid',
            status__in=['confirmed', 'pending']
        ).count()
        
        # Get available courses for enrollment
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
        
        # Get dashboard page content if available
        from .models import PageContent
        try:
            dashboard_content = PageContent.objects.get(page_type='student_dashboard', is_active=True)
            context['dashboard_content'] = dashboard_content
        except PageContent.DoesNotExist:
            context['dashboard_content'] = None
        
        # Enhanced statistics for dashboard
        context['stats'] = {
            'total_courses': context['total_enrollments'],
            'active_courses': context['confirmed_enrollments'],
            'pending_courses': context['pending_enrollments'],
            'completed_courses': context['completed_enrollments'],
            'cancelled_courses': context['cancelled_enrollments'],
            'paid_courses': context['paid_enrollments'],
            'unpaid_courses': context['unpaid_enrollments'],
            'overdue_payments': context['overdue_payments'],
            'profile_completion': self._calculate_profile_completion(student),
        }
        
        # Learning progress
        total_confirmed = context['confirmed_enrollments'] + context['completed_enrollments']
        if total_confirmed > 0:
            context['learning_progress'] = {
                'completion_rate': int((context['completed_enrollments'] / total_confirmed) * 100),
                'active_rate': int((context['confirmed_enrollments'] / total_confirmed) * 100),
            }
        else:
            context['learning_progress'] = {'completion_rate': 0, 'active_rate': 0}
        
        return context
    
    def _calculate_profile_completion(self, student):
        """Calculate profile completion percentage"""
        fields_to_check = [
            student.phone_number, 
            student.date_of_birth, 
            student.address, 
            student.english_level, 
            student.goals
        ]
        completed_fields = sum(1 for field in fields_to_check if field)
        return int((completed_fields / len(fields_to_check)) * 100)


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

