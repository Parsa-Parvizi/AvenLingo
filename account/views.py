from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, TemplateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect, JsonResponse, Http404
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied, ValidationError
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
import logging

from .models import User, Student, Teacher, TeacherApplication
from .forms import (
    StudentRegistrationForm, TeacherRegistrationForm, CustomLoginForm,
    TeacherApplicationForm, StudentProfileForm, TeacherProfileForm,
    CustomPasswordResetForm, CustomSetPasswordForm
)
from .services import (
    UserRegistrationService, TeacherApplicationService, 
    EmailService, UserProfileService
)

logger = logging.getLogger(__name__)


class StudentRegistrationView(CreateView):
    """Enhanced student registration view with service layer integration"""
    model = User
    form_class = StudentRegistrationForm
    template_name = 'account/student_register.html'
    success_url = reverse_lazy('account:email_verification')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        try:
            # Form save method handles service layer integration
            user = form.save()
            
            # Enhanced success message
            user_name = form.cleaned_data.get('first_name', 'کاربر')
            messages.success(
                self.request,
                f'{user_name} عزیز، حساب کاربری شما با موفقیت ایجاد شد. '
                f'لطفاً ایمیل خود را برای فعال‌سازی حساب تایید کنید.'
            )
            
            # Log successful registration
            logger.info(f'Student registered successfully: {form.cleaned_data["email"]}')
            
            return redirect(self.success_url)
            
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f'Unexpected error in student registration: {str(e)}')
            messages.error(self.request, 'خطای غیرمنتظره. لطفاً دوباره تلاش کنید.')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'ثبت‌نام دانش‌آموز',
            'breadcrumb': [
                {'title': 'خانه', 'url': '/'},
                {'title': 'ثبت‌نام دانش‌آموز', 'url': None}
            ]
        })
        return context


class TeacherRegistrationView(CreateView):
    """Enhanced teacher registration view for approved applications"""
    model = User
    form_class = TeacherRegistrationForm
    template_name = 'account/teacher_register.html'
    success_url = reverse_lazy('account:login')
    
    def dispatch(self, request, *args, **kwargs):
        self.email = kwargs.get('email')
        
        # Check if teacher registration is eligible
        self.application = TeacherApplicationService.check_registration_eligibility(self.email)
        
        if not self.application:
            messages.error(
                request, 
                'درخواست تایید شده‌ای برای این ایمیل یافت نشد یا منقضی شده است.'
            )
            return redirect('account:teacher_apply')
        
        # Check if teacher account already exists
        if Teacher.objects.filter(application=self.application).exists():
            messages.error(request, 'حساب کاربری برای این درخواست قبلاً ایجاد شده است.')
            return redirect('account:login')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['application'] = self.application
        return kwargs
    
    def form_valid(self, form):
        try:
            # Form save method handles service layer integration
            user = form.save()
            
            messages.success(
                self.request,
                f'حساب کاربری شما با موفقیت ایجاد شد. '
                f'خوش آمدید {user.get_full_name()}!'
            )
            
            logger.info(f'Teacher registered successfully: {user.email}')
            return redirect('account:login')
            
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f'Unexpected error in teacher registration: {str(e)}')
            messages.error(self.request, 'خطای غیرمنتظره. لطفاً دوباره تلاش کنید.')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'ثبت‌نام معلم',
            'application': self.application,
            'breadcrumb': [
                {'title': 'خانه', 'url': '/'},
                {'title': 'ثبت‌نام معلم', 'url': None}
            ]
        })
        return context


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
            return reverse_lazy('dashboard:dashboard_home')
        elif user.user_type == 'teacher':
            return reverse_lazy('dashboard:teacher_dashboard')
        elif user.user_type == 'admin':
            return reverse_lazy('admin:index')
        return reverse_lazy('dashboard:dashboard_home')
    
    def form_valid(self, form):
        # Check if user is active (email verified)
        user = form.get_user()
        if not user.is_active:
            messages.error(self.request, 'حساب کاربری شما فعال نیست. لطفاً ایمیل خود را تایید کنید.')
            logout(self.request)
            return redirect('account:email_verification')
        
        # Enhanced security logging
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
            return redirect('dashboard:dashboard_home')
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
    """Enhanced teacher application view with improved validation"""
    model = TeacherApplication
    form_class = TeacherApplicationForm
    template_name = 'account/teacher_apply.html'
    success_url = reverse_lazy('account:teacher_apply_success')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        try:
            # Form save method handles service layer integration
            application = form.save()
            
            messages.success(
                self.request,
                'درخواست همکاری شما با موفقیت ارسال شد. '
                'پس از بررسی، نتیجه از طریق ایمیل اطلاع داده خواهد شد.'
            )
            
            logger.info(f'Teacher application submitted: {application.email}')
            return redirect(self.success_url)
            
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f'Unexpected error in teacher application: {str(e)}')
            messages.error(self.request, 'خطای غیرمنتظره. لطفاً دوباره تلاش کنید.')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'درخواست همکاری معلم',
            'breadcrumb': [
                {'title': 'خانه', 'url': '/'},
                {'title': 'درخواست همکاری', 'url': None}
            ]
        })
        return context


class TeacherApplicationSuccessView(TemplateView):
    """Success page after teacher application submission"""
    template_name = 'account/teacher_apply_success.html'


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
def verify_email(request, user_id, token):
    """Enhanced email verification view"""
    try:
        success = UserRegistrationService.verify_student_email(user_id, token)
        
        if success:
            messages.success(
                request,
                'ایمیل شما با موفقیت تایید شد. حساب کاربری شما فعال شده است.'
            )
            return redirect('account:login')
        else:
            messages.error(
                request,
                'لینک تایید نامعتبر یا منقضی شده است. لطفاً دوباره درخواست کنید.'
            )
            return redirect('account:email_verification')
            
    except Exception as e:
        logger.error(f'Error in email verification: {str(e)}')
        messages.error(request, 'خطا در تایید ایمیل. لطفاً دوباره تلاش کنید.')
        return redirect('account:email_verification')


class EmailVerificationView(LoginRequiredMixin, TemplateView):
    """Enhanced email verification view"""
    template_name = 'account/email_verification.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'user': self.request.user,
            'page_title': 'تایید ایمیل',
            'can_resend': not self.request.user.is_email_verified
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Resend verification email"""
        user = request.user
        
        if user.is_email_verified:
            messages.info(request, 'ایمیل شما قبلاً تایید شده است.')
            return redirect('account:dashboard')
        
        try:
            # Check rate limiting (one email per 5 minutes)
            from django.core.cache import cache
            cache_key = f'email_verification_rate_limit_{user.id}'
            
            if cache.get(cache_key):
                messages.warning(
                    request,
                    'شما اخیراً ایمیل تایید دریافت کرده‌اید. لطفاً چند دقیقه صبر کنید.'
                )
                return redirect('account:email_verification')
            
            # Generate new token and send email
            token = user.generate_email_verification_token()
            EmailService.send_student_verification_email(user, token)
            
            # Set rate limit
            cache.set(cache_key, True, 300)  # 5 minutes
            
            messages.success(
                request,
                'ایمیل تایید ارسال شد. لطفاً صندوق ورودی خود را بررسی کنید.'
            )
            
        except Exception as e:
            logger.error(f'Error resending verification email: {str(e)}')
            messages.error(request, 'خطا در ارسال ایمیل. لطفاً دوباره تلاش کنید.')
        
        return redirect('account:email_verification')


# Admin Views for Teacher Applications
@method_decorator(login_required, name='dispatch')
class TeacherApplicationListView(UserPassesTestMixin, TemplateView):
    """Enhanced admin view for managing teacher applications"""
    template_name = 'account/admin/teacher_applications.html'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_admin_user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get applications with filtering
        status_filter = self.request.GET.get('status', 'all')
        
        applications = TeacherApplication.objects.all()
        if status_filter != 'all':
            applications = applications.filter(status=status_filter)
        
        context.update({
            'page_title': 'مدیریت درخواست‌های همکاری',
            'pending_applications': applications.filter(status='pending').order_by('-submitted_at'),
            'accepted_applications': applications.filter(status='accepted').order_by('-reviewed_at'),
            'rejected_applications': applications.filter(status='rejected').order_by('-reviewed_at'),
            'status_filter': status_filter,
            'status_choices': TeacherApplication.STATUS_CHOICES
        })
        return context


@method_decorator(login_required, name='dispatch')
class TeacherApplicationDetailView(UserPassesTestMixin, DetailView):
    """Enhanced admin view to view teacher application details"""
    model = TeacherApplication
    template_name = 'account/admin/teacher_application_detail.html'
    context_object_name = 'application'
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_admin_user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'جزئیات درخواست همکاری',
            'breadcrumb': [
                {'title': 'مدیریت', 'url': '/admin/'},
                {'title': 'درخواست‌های همکاری', 'url': reverse_lazy('account:admin_teacher_applications')},
                {'title': 'جزئیات درخواست', 'url': None}
            ]
        })
        return context


@method_decorator(login_required, name='dispatch')
class TeacherApplicationApprovalView(UserPassesTestMixin, TemplateView):
    """Enhanced admin view to approve/reject teacher applications"""
    
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_admin_user
    
    def post(self, request, pk):
        try:
            application = get_object_or_404(TeacherApplication, pk=pk)
            action = request.POST.get('action')
            admin_notes = request.POST.get('admin_notes', '').strip()
            
            if action == 'accept':
                TeacherApplicationService.approve_application(
                    application=application,
                    reviewed_by=request.user,
                    admin_notes=admin_notes
                )
                messages.success(
                    request,
                    f'درخواست {application.first_name} {application.last_name} پذیرفته شد. '
                    f'ایمیل تایید برای معلم ارسال شده است.'
                )
                
            elif action == 'reject':
                if not admin_notes:
                    messages.error(request, 'لطفاً دلیل رد درخواست را وارد کنید.')
                    return redirect('account:admin_teacher_applications')
                
                TeacherApplicationService.reject_application(
                    application=application,
                    reviewed_by=request.user,
                    admin_notes=admin_notes
                )
                messages.success(
                    request,
                    f'درخواست {application.first_name} {application.last_name} رد شد.'
                )
            else:
                messages.error(request, 'عملیات نامعتبر.')
            
        except Exception as e:
            logger.error(f'Error in application approval: {str(e)}')
            messages.error(request, 'خطا در پردازش درخواست.')
        
        return redirect('account:admin_teacher_applications')


# Profile Views
class StudentProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Enhanced student profile view"""
    model = Student
    form_class = StudentProfileForm
    template_name = 'account/student_profile.html'
    success_url = reverse_lazy('dashboard:dashboard_home')
    
    def test_func(self):
        return self.request.user.is_student
    
    def get_object(self):
        return get_object_or_404(Student, user=self.request.user)
    
    def form_valid(self, form):
        try:
            # Use service layer for profile updates
            student = UserProfileService.update_student_profile(
                student=self.get_object(),
                **form.cleaned_data
            )
            
            messages.success(self.request, 'پروفایل شما با موفقیت بروزرسانی شد.')
            return redirect(self.success_url)
            
        except Exception as e:
            logger.error(f'Error updating student profile: {str(e)}')
            messages.error(self.request, 'خطا در بروزرسانی پروفایل.')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_object()
        context.update({
            'page_title': 'ویرایش پروفایل',
            'completion_percentage': student.get_profile_completion_percentage(),
            'breadcrumb': [
                {'title': 'داشبورد', 'url': reverse_lazy('dashboard:dashboard_home')},
                {'title': 'ویرایش پروفایل', 'url': None}
            ]
        })
        return context


class TeacherProfileView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Enhanced teacher profile view"""
    model = Teacher
    form_class = TeacherProfileForm
    template_name = 'account/teacher_profile.html'
    success_url = reverse_lazy('dashboard:teacher_dashboard')
    
    def test_func(self):
        return self.request.user.is_teacher
    
    def get_object(self):
        return get_object_or_404(Teacher, user=self.request.user)
    
    def form_valid(self, form):
        try:
            # Use service layer for profile updates
            teacher = UserProfileService.update_teacher_profile(
                teacher=self.get_object(),
                **form.cleaned_data
            )
            
            messages.success(self.request, 'پروفایل شما با موفقیت بروزرسانی شد.')
            return redirect(self.success_url)
            
        except Exception as e:
            logger.error(f'Error updating teacher profile: {str(e)}')
            messages.error(self.request, 'خطا در بروزرسانی پروفایل.')
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher = self.get_object()
        context.update({
            'page_title': 'ویرایش پروفایل',
            'completion_percentage': teacher.get_profile_completion_percentage(),
            'breadcrumb': [
                {'title': 'داشبورد', 'url': reverse_lazy('dashboard:teacher_dashboard')},
                {'title': 'ویرایش پروفایل', 'url': None}
            ]
        })
        return context


# AJAX Views
@csrf_exempt
@require_http_methods(["POST"])
def validate_email(request):
    """Enhanced AJAX view to check email availability"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        
        if not email:
            return JsonResponse({
                'available': False,
                'message': 'ایمیل وارد نشده است'
            })
        
        # Check email format
        from django.core.validators import validate_email as django_validate_email
        try:
            django_validate_email(email)
        except ValidationError:
            return JsonResponse({
                'available': False,
                'message': 'فرمت ایمیل معتبر نیست'
            })
        
        # Check availability
        email_exists = User.objects.filter(email=email).exists()
        application_exists = TeacherApplication.objects.for_email(email).exists()
        
        if email_exists:
            return JsonResponse({
                'available': False,
                'message': 'این ایمیل قبلاً ثبت شده است'
            })
        elif application_exists:
            return JsonResponse({
                'available': False,
                'message': 'این ایمیل برای درخواست همکاری استفاده شده است'
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
        logger.error(f'Error in email validation AJAX: {str(e)}')
        return JsonResponse({
            'available': False,
            'message': 'خطا در بررسی ایمیل'
        }, status=500)


# Public view for checking teacher registration eligibility
def check_teacher_registration(request, email):
    """Enhanced view to check teacher registration eligibility"""
    try:
        application = TeacherApplicationService.check_registration_eligibility(email)
        
        if not application:
            messages.error(
                request,
                'درخواست تایید شده‌ای برای این ایمیل یافت نشد یا منقضی شده است.'
            )
            return redirect('account:teacher_apply')
        
        # Check if teacher account already exists
        if Teacher.objects.filter(application=application).exists():
            messages.error(request, 'حساب کاربری برای این ایمیل قبلاً ایجاد شده است.')
            return redirect('account:login')
        
        return redirect('account:teacher_register', email=email)
        
    except Exception as e:
        logger.error(f'Error checking teacher registration eligibility: {str(e)}')
        messages.error(request, 'خطا در بررسی واجد شرایط بودن.')
        return redirect('account:teacher_apply')

