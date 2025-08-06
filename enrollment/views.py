from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import json
import logging

from .models import Enrollment, EnrollmentHistory
from course.models import Course
from account.models import Student

# Set up logging
logger = logging.getLogger('enrollment')


class StudentRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure only students can access the view"""
    def test_func(self):
        return (self.request.user.is_authenticated and 
                hasattr(self.request.user, 'user_type') and 
                self.request.user.user_type == 'student')
    
    def handle_no_permission(self):
        messages.error(self.request, 'شما باید به عنوان دانش‌آموز وارد شوید.')
        return redirect('account:login')


class StudentEnrollmentListView(StudentRequiredMixin, ListView):
    """List all enrollments for the current student"""
    model = Enrollment
    template_name = 'enrollment/student_enrollments.html'
    context_object_name = 'enrollments'
    paginate_by = 10
    
    def get_queryset(self):
        student = get_object_or_404(Student, user=self.request.user)
        return Enrollment.objects.filter(student=student).select_related(
            'course', 'course__teacher', 'course__category'
        ).order_by('-enrolled_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = get_object_or_404(Student, user=self.request.user)
        
        # Add statistics
        enrollments = self.get_queryset()
        context.update({
            'student': student,
            'total_enrollments': enrollments.count(),
            'pending_enrollments': enrollments.filter(status='pending').count(),
            'confirmed_enrollments': enrollments.filter(status='confirmed').count(),
            'cancelled_enrollments': enrollments.filter(status='cancelled').count(),
        })
        
        return context


class EnrollmentDetailView(StudentRequiredMixin, DetailView):
    """Detailed view of a specific enrollment"""
    model = Enrollment
    template_name = 'enrollment/enrollment_detail.html'
    context_object_name = 'enrollment'
    
    def get_queryset(self):
        student = get_object_or_404(Student, user=self.request.user)
        return Enrollment.objects.filter(student=student).select_related(
            'course', 'course__teacher', 'course__category'
        ).prefetch_related('history')


class CourseEnrollmentView(StudentRequiredMixin, CreateView):
    """Enroll a student in a course"""
    model = Enrollment
    fields = ['note']
    template_name = 'enrollment/course_enrollment.html'
    
    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, id=kwargs['course_id'], is_active=True)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        return context
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                student = get_object_or_404(Student, user=self.request.user)
                
                # Check if already enrolled
                if Enrollment.objects.filter(student=student, course=self.course).exists():
                    messages.error(self.request, 'شما قبلاً در این دوره ثبت‌نام کرده‌اید.')
                    return redirect('course:course_detail', pk=self.course.id)
                
                # Check course capacity
                if self.course.is_full:
                    messages.error(self.request, 'ظرفیت این دوره تکمیل شده است.')
                    return redirect('course:course_detail', pk=self.course.id)
                
                # Create enrollment
                enrollment = form.save(commit=False)
                enrollment.student = student
                enrollment.course = self.course
                enrollment.enrollment_source = 'website'
                enrollment.save()
                
                # Log the enrollment
                logger.info(f"New enrollment created: {enrollment} by user {self.request.user.username}")
                
                messages.success(
                    self.request, 
                    f'ثبت‌نام شما در دوره "{self.course.title}" با موفقیت انجام شد. '
                    'پس از بررسی و تأیید، از طریق ایمیل یا تماس اطلاع‌رسانی خواهید شد.'
                )
                
                return redirect('enrollment:enrollment_detail', pk=enrollment.id)
                
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"Error during enrollment: {e}")
            messages.error(self.request, 'خطایی در فرآیند ثبت‌نام رخ داد. لطفاً دوباره تلاش کنید.')
            return self.form_invalid(form)


@login_required
@require_POST
@csrf_protect
def cancel_enrollment(request, enrollment_id):
    """AJAX view to cancel an enrollment"""
    try:
        student = get_object_or_404(Student, user=request.user)
        enrollment = get_object_or_404(Enrollment, id=enrollment_id, student=student)
        
        if not enrollment.can_be_cancelled:
            return JsonResponse({
                'success': False,
                'message': 'این ثبت‌نام قابل لغو نیست.'
            })
        
        # Get cancellation reason from request
        data = json.loads(request.body) if request.body else {}
        reason = data.get('reason', 'لغو توسط دانش‌آموز')
        
        # Cancel enrollment
        if enrollment.cancel_enrollment(reason=reason, cancelled_by=request.user.username):
            
            # Create history record
            EnrollmentHistory.objects.create(
                enrollment=enrollment,
                old_status='confirmed',
                new_status='cancelled',
                changed_by=request.user.username,
                reason=reason
            )
            
            logger.info(f"Enrollment cancelled: {enrollment} by user {request.user.username}")
            
            return JsonResponse({
                'success': True,
                'message': 'ثبت‌نام شما با موفقیت لغو شد.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'خطا در لغو ثبت‌نام.'
            })
            
    except Exception as e:
        logger.error(f"Error cancelling enrollment: {e}")
        return JsonResponse({
            'success': False,
            'message': 'خطایی رخ داد. لطفاً دوباره تلاش کنید.'
        })


@login_required
def enrollment_certificate(request, enrollment_id):
    """Generate enrollment certificate (placeholder)"""
    try:
        student = get_object_or_404(Student, user=request.user)
        enrollment = get_object_or_404(
            Enrollment, 
            id=enrollment_id, 
            student=student, 
            status='completed'
        )
        
        # This is a placeholder - you would implement actual certificate generation here
        # For now, just return a simple response
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="certificate_{enrollment.id}.txt"'
        response.write(f'گواهی تکمیل دوره\n\n')
        response.write(f'دانش‌آموز: {enrollment.student.user.get_full_name()}\n')
        response.write(f'دوره: {enrollment.course.title}\n')
        response.write(f'مدرس: {enrollment.course.teacher}\n')
        response.write(f'تاریخ تکمیل: {enrollment.confirmed_at}\n')
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating certificate: {e}")
        messages.error(request, 'خطا در تولید گواهی.')
        return redirect('enrollment:student_enrollments')


class QuickEnrollView(StudentRequiredMixin, CreateView):
    """Quick enrollment for AJAX requests"""
    model = Enrollment
    fields = []
    
    def post(self, request, *args, **kwargs):
        try:
            course_id = request.POST.get('course_id')
            course = get_object_or_404(Course, id=course_id, is_active=True)
            student = get_object_or_404(Student, user=request.user)
            
            # Check if already enrolled
            if Enrollment.objects.filter(student=student, course=course).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'شما قبلاً در این دوره ثبت‌نام کرده‌اید.'
                })
            
            # Check course capacity
            if course.is_full:
                return JsonResponse({
                    'success': False,
                    'message': 'ظرفیت این دوره تکمیل شده است.'
                })
            
            # Create enrollment
            with transaction.atomic():
                enrollment = Enrollment.objects.create(
                    student=student,
                    course=course,
                    enrollment_source='website'
                )
                
                logger.info(f"Quick enrollment created: {enrollment} by user {request.user.username}")
                
                return JsonResponse({
                    'success': True,
                    'message': f'ثبت‌نام در دوره "{course.title}" با موفقیت انجام شد.',
                    'enrollment_id': enrollment.id
                })
                
        except Exception as e:
            logger.error(f"Error in quick enrollment: {e}")
            return JsonResponse({
                'success': False,
                'message': 'خطایی رخ داد. لطفاً دوباره تلاش کنید.'
            })


# Course browsing and filtering views for enrollment
class AvailableCoursesView(LoginRequiredMixin, ListView):
    """List available courses for enrollment"""
    model = Course
    template_name = 'enrollment/available_courses.html'
    context_object_name = 'courses'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Course.objects.filter(
            is_active=True,
            status='published'
        ).select_related('teacher', 'category').order_by('-created_at')
        
        # Filter out courses the student is already enrolled in
        if hasattr(self.request.user, 'user_type') and self.request.user.user_type == 'student':
            try:
                student = Student.objects.get(user=self.request.user)
                enrolled_course_ids = Enrollment.objects.filter(
                    student=student,
                    status__in=['pending', 'confirmed']
                ).values_list('course_id', flat=True)
                queryset = queryset.exclude(id__in=enrolled_course_ids)
            except Student.DoesNotExist:
                pass
        
        # Apply filters
        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level=level)
            
        class_type = self.request.GET.get('class_type')
        if class_type:
            queryset = queryset.filter(class_type=class_type)
            
        language = self.request.GET.get('language')
        if language:
            queryset = queryset.filter(category__language=language)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        from course.models import LANGUAGE_CHOICES
        context.update({
            'level_choices': Course.LEVEL_CHOICES,
            'class_type_choices': Course.CLASS_TYPE_CHOICES,
            'language_choices': LANGUAGE_CHOICES,
            'current_filters': {
                'level': self.request.GET.get('level', ''),
                'class_type': self.request.GET.get('class_type', ''),
                'language': self.request.GET.get('language', ''),
            }
        })
        
        return context
