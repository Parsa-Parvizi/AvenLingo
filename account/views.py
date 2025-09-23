from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, TemplateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
import secrets
import json

from .models import User, Student, Teacher, TeacherApplication
from .forms import (
    StudentRegistrationForm, TeacherRegistrationForm, CustomLoginForm,
    TeacherApplicationForm, StudentProfileForm, TeacherProfileForm,
    CustomPasswordResetForm, CustomSetPasswordForm
)


class StudentRegistrationView(CreateView):
    """Enhanced registration view for students with security features"""
    model = User
    form_class = StudentRegistrationForm
    template_name = 'account/student_register.html'
    success_url = reverse_lazy('account:email_verification')
    
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
        
        # Set user as inactive until email verification
        user = form.instance
        user.is_active = False  # Will be activated after email verification
        user.save(update_fields=['is_active'])
        
        # Send verification email
        self.send_welcome_email(user)
        
        # Enhanced success message with user's name
        user_name = form.cleaned_data.get('first_name', 'کاربر')
        messages.success(
            self.request,
            f'{user_name} عزیز، حساب کاربری شما با موفقیت ایجاد شد. لطفاً ایمیل خود را تایید کنید.'
        )
        
        # Log successful registration
        import logging
        logger = logging.getLogger('account.registration')
        logger.info(f'Student registered successfully: {form.cleaned_data["email"]}')
        
        return response
    
    def send_welcome_email(self, user):
        """Send welcome email with verification link"""
        token = secrets.token_urlsafe(32)
        user.email_verification_token = token
        user.save(update_fields=['email_verification_token'])
        
        current_site = get_current_site(self.request)
        verification_url = f"http://{current_site.domain}/auth/verify-email/{user.id}/{token}/"
        
        subject = 'خوش آمدید به آکادمی زبان مبینا - تایید ایمیل'
        message = render_to_string('account/welcome_email.html', {
            'user': user,
            'verification_url': verification_url,
            'site_name': current_site.name,
        })
        
        send_mail(
            subject=subject,
            message=message,
            from_email='noreply@academy.com',
            recipient_list=[user.email],
            fail_silently=False,
        )
    
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
        # Check if user is active (email verified)
        user = form.get_user()
        if not user.is_active:
            messages.error(self.request, 'حساب کاربری شما فعال نیست. لطفاً ایمیل خود را تایید کنید.')
            logout(self.request)
            return redirect('account:email_verification')
        
        # Enhanced security logging
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
    
    def dispatch(self, request, *args, **kwargs):
        # Ensure student profile exists (create if missing)
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
    """Enhanced dashboard for teachers"""
    template_name = 'account/teacher_dashboard.html'
    
    def test_func(self):
        return self.request.user.user_type == 'teacher'
    
    def handle_no_permission(self):
        from django.contrib import messages
        messages.error(self.request, 'دسترسی غیرمجاز به داشبورد مدرس.')
        return redirect('account:dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        # Ensure teacher profile exists, otherwise guide user instead of 404
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
        
        # Get teacher's courses and students
        from course.models import Course
        from enrollment.models import Enrollment
        
        courses = Course.objects.filter(teacher=teacher, is_active=True).select_related('category')
        context['courses'] = courses
        
        # Calculate total students across all courses
        total_students = sum(course.students.count() for course in courses)
        context['total_students'] = total_students
        
        # Get recent enrollments
        recent_enrollments = Enrollment.objects.filter(
            course__teacher=teacher
        ).select_related('student__user', 'course').order_by('-enrolled_at')[:5]
        context['recent_enrollments'] = recent_enrollments
        
        # Get course statistics
        context['course_stats'] = {
            'total_courses': courses.count(),
            'published_courses': courses.filter(status='published').count(),
            'draft_courses': courses.filter(status='draft').count(),
            'total_students': total_students,
            'active_students': sum(
                course.students.filter(
                    enrollments__status='confirmed'
                ).count() for course in courses
            )
        }
        
        # Get recent activities
        context['recent_activities'] = self.get_recent_activities(teacher)
        
        return context
    
    def get_recent_activities(self, teacher):
        """Get recent activities for teacher dashboard"""
        from enrollment.models import Enrollment
        from course.models import Course
        
        activities = []
        
        # Recent course creations
        recent_courses = Course.objects.filter(
            teacher=teacher
        ).order_by('-created_at')[:3]
        
        for course in recent_courses:
            activities.append({
                'type': 'course_created',
                'title': f'دوره "{course.title}" ایجاد شد',
                'date': course.created_at,
                'icon': 'fas fa-book',
                'color': 'primary'
            })
        
        # Recent enrollments
        recent_enrollments = Enrollment.objects.filter(
            course__teacher=teacher
        ).select_related('student__user', 'course').order_by('-enrolled_at')[:3]
        
        for enrollment in recent_enrollments:
            activities.append({
                'type': 'student_enrolled',
                'title': f'{enrollment.student.user.get_full_name()} در دوره "{enrollment.course.title}" ثبت‌نام کرد',
                'date': enrollment.enrolled_at,
                'icon': 'fas fa-user-plus',
                'color': 'success'
            })
        
        # Sort activities by date
        activities.sort(key=lambda x: x['date'], reverse=True)
        return activities[:5]


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


# Password Reset Views
class CustomPasswordResetView(PasswordResetView):
    """Enhanced password reset view with security features"""
    template_name = 'account/password_reset.html'
    email_template_name = 'account/password_reset_email.html'
    subject_template_name = 'account/password_reset_subject.txt'
    success_url = reverse_lazy('account:password_reset_done')
    form_class = CustomPasswordResetForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'بازیابی رمز عبور'
        return context
    
    def form_valid(self, form):
        # Rate limiting for password reset
        email = form.cleaned_data['email']
        if self.check_rate_limit(email):
            messages.error(self.request, 'تعداد درخواست‌های شما زیاد است. لطفاً ۱۵ دقیقه صبر کنید.')
            return self.form_invalid(form)
        
        # Log password reset request
        import logging
        logger = logging.getLogger('account.password_reset')
        logger.info(f'Password reset requested for: {email} from IP: {self.get_client_ip()}')
        
        return super().form_valid(form)
    
    def check_rate_limit(self, email):
        """Check rate limit for password reset requests"""
        cache_key = f'password_reset_rate_limit_{email}'
        from django.core.cache import cache
        
        if cache.get(cache_key):
            return True
        
        cache.set(cache_key, True, 900)  # 15 minutes
        return False
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Enhanced password reset done view"""
    template_name = 'account/password_reset_done.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'ایمیل ارسال شد'
        return context


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Enhanced password reset confirm view"""
    template_name = 'account/password_reset_confirm.html'
    success_url = reverse_lazy('account:password_reset_complete')
    form_class = CustomSetPasswordForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'تغییر رمز عبور'
        return context


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Enhanced password reset complete view"""
    template_name = 'account/password_reset_complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'رمز عبور تغییر یافت'
        return context


# Email Verification Views
class EmailVerificationView(LoginRequiredMixin, TemplateView):
    """View for email verification"""
    template_name = 'account/email_verification.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['page_title'] = 'تایید ایمیل'
        return context
    
    def post(self, request, *args, **kwargs):
        """Send verification email"""
        user = request.user
        
        if user.is_email_verified:
            messages.info(request, 'ایمیل شما قبلاً تایید شده است.')
            return redirect('account:dashboard')
        
        # Generate verification token
        token = self.generate_verification_token(user)
        
        # Send verification email
        self.send_verification_email(user, token)
        
        messages.success(request, 'ایمیل تایید ارسال شد. لطفاً صندوق ورودی خود را بررسی کنید.')
        return redirect('account:email_verification')
    
    def generate_verification_token(self, user):
        """Generate email verification token"""
        token = secrets.token_urlsafe(32)
        user.email_verification_token = token
        user.save(update_fields=['email_verification_token'])
        return token
    
    def send_verification_email(self, user, token):
        """Send verification email"""
        current_site = get_current_site(self.request)
        verification_url = f"http://{current_site.domain}/auth/verify-email/{user.id}/{token}/"
        
        subject = 'تایید ایمیل - آکادمی زبان مبینا'
        message = render_to_string('account/email_verification_email.html', {
            'user': user,
            'verification_url': verification_url,
            'site_name': current_site.name,
        })
        
        send_mail(
            subject=subject,
            message=message,
            from_email='noreply@academy.com',
            recipient_list=[user.email],
            fail_silently=False,
        )


def verify_email(request, user_id, token):
    """Verify email with token"""
    try:
        user = User.objects.get(id=user_id, email_verification_token=token)
        
        if user.is_email_verified:
            messages.info(request, 'ایمیل شما قبلاً تایید شده است.')
        else:
            user.is_email_verified = True
            user.is_active = True  # Activate user after email verification
            user.email_verification_token = ''
            user.save(update_fields=['is_email_verified', 'is_active', 'email_verification_token'])
            
            messages.success(request, 'ایمیل شما با موفقیت تایید شد! حالا می‌توانید وارد شوید.')
            
            # Log successful verification
            import logging
            logger = logging.getLogger('account.email_verification')
            logger.info(f'Email verified successfully for: {user.email}')
        
        return redirect('account:login')
        
    except User.DoesNotExist:
        messages.error(request, 'لینک تایید نامعتبر است.')
        return redirect('account:login')


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


@csrf_exempt
@require_http_methods(["POST"])
def validate_email(request):
    """
    AJAX view to check if an email is available for registration
    """
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        
        if not email:
            return JsonResponse({
                'available': False,
                'message': 'ایمیل وارد نشده است'
            })
        
        # Check if email already exists
        email_exists = User.objects.filter(email=email).exists()
        
        if email_exists:
            return JsonResponse({
                'available': False,
                'message': 'این ایمیل قبلاً ثبت شده است'
            })
        else:
            return JsonResponse({
                'available': True,
                'message': 'ایمیل در دسترس است'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'available': False,
            'message': 'درخواست نامعتبر'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'available': False,
            'message': 'خطا در بررسی ایمیل'
        }, status=500)

