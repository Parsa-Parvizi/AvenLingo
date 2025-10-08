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
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, 'user_type') and self.request.user.user_type == 'teacher':
                messages.error(self.request, 'این صفحه فقط برای زبان‌آموزان است. شما به عنوان معلم وارد شده‌اید.')
            elif self.request.user.is_staff or self.request.user.is_superuser:
                messages.error(self.request, 'این صفحه فقط برای زبان‌آموزان است. شما به عنوان ادمین وارد شده‌اید.')
            else:
                messages.error(self.request, 'شما باید به عنوان دانش‌آموز وارد شوید.')
            return redirect('core:home')
        else:
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


class CourseEnrollmentView(LoginRequiredMixin, CreateView):
    """Enroll a student in a course - with strict student-only check"""
    model = Enrollment
    fields = ['note', 'payment_receipt']
    template_name = 'enrollment/course_enrollment.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Must be authenticated
        if not request.user.is_authenticated:
            messages.warning(request, 'برای ثبت‌نام در دوره باید وارد حساب کاربری خود شوید.')
            return redirect(f"{reverse('account:login')}?next={request.path}")
        
        # Must be student (not admin, not teacher)
        if not hasattr(request.user, 'user_type') or request.user.user_type != 'student':
            if request.user.user_type == 'teacher':
                messages.error(request, 'فقط زبان‌آموزان می‌توانند در دوره‌ها ثبت‌نام کنند. شما به عنوان معلم وارد شده‌اید.')
            elif request.user.is_staff or request.user.is_superuser:
                messages.error(request, 'فقط زبان‌آموزان می‌توانند در دوره‌ها ثبت‌نام کنند. شما به عنوان ادمین وارد شده‌اید.')
            else:
                messages.error(request, 'فقط زبان‌آموزان می‌توانند در دوره‌ها ثبت‌نام کنند.')
            return redirect('course:all-courses')
        
        self.course = get_object_or_404(Course, slug=kwargs['course_slug'], is_active=True)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.course
        
        # Check if student already has pending enrollment
        if hasattr(self.request.user, 'student_profile'):
            existing_enrollment = Enrollment.objects.filter(
                student=self.request.user.student_profile,
                course=self.course
            ).first()
            context['existing_enrollment'] = existing_enrollment
        
        return context
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                student = get_object_or_404(Student, user=self.request.user)
                
                # Check if already enrolled
                existing = Enrollment.objects.filter(student=student, course=self.course).first()
                if existing:
                    if existing.status == 'pending':
                        messages.warning(self.request, 'شما قبلاً در این دوره ثبت‌نام کرده‌اید و در انتظار تأیید هستید.')
                        return redirect('enrollment:upload-receipt', enrollment_id=existing.id)
                    elif existing.status == 'confirmed':
                        messages.info(self.request, 'شما قبلاً در این دوره ثبت‌نام تأیید شده دارید.')
                        return redirect('enrollment:enrollment_detail', pk=existing.id)
                    else:
                        messages.error(self.request, 'شما قبلاً در این دوره ثبت‌نام کرده‌اید.')
                        return redirect('course:detail', slug=self.course.slug)
                
                # Check course capacity (only confirmed enrollments count)
                confirmed_count = self.course.enrollments.filter(status='confirmed').count()
                if confirmed_count >= self.course.capacity:
                    messages.error(self.request, 'متأسفانه ظرفیت این دوره تکمیل شده است.')
                    return redirect('course:detail', slug=self.course.slug)
                
                # Create enrollment in PENDING status
                enrollment = form.save(commit=False)
                enrollment.student = student
                enrollment.course = self.course
                enrollment.enrollment_source = 'website'
                enrollment.status = 'pending'  # Important: stays pending until admin confirms
                enrollment.save()
                
                # Log the enrollment
                logger.info(f"New enrollment created: {enrollment} by user {self.request.user.email}")
                
                # Determine next step based on course type
                if self.course.is_free:
                    messages.success(
                        self.request, 
                        f'ثبت‌نام شما در دوره رایگان "{self.course.title}" با موفقیت ثبت شد. '
                        'در انتظار تأیید مدیریت هستید.',
                        extra_tags='enrollment'
                    )
                    return redirect('dashboard:student_dashboard')
                else:
                    messages.success(
                        self.request, 
                        f'ثبت‌نام شما در دوره "{self.course.title}" با موفقیت ثبت شد. '
                        'لطفاً فیش واریزی خود را آپلود کنید.',
                        extra_tags='enrollment'
                    )
                    return redirect('enrollment:upload-receipt', enrollment_id=enrollment.id)
                
        except ValidationError as e:
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"Error during enrollment: {e}")
            messages.error(self.request, 'خطایی در فرآیند ثبت‌نام رخ داد. لطفاً دوباره تلاش کنید.')
            return self.form_invalid(form)


class UploadReceiptView(StudentRequiredMixin, UpdateView):
    """Upload payment receipt for pending enrollment"""
    model = Enrollment
    fields = ['payment_receipt', 'note']
    template_name = 'enrollment/upload_receipt.html'
    pk_url_kwarg = 'enrollment_id'
    
    def get_queryset(self):
        student = get_object_or_404(Student, user=self.request.user)
        return Enrollment.objects.filter(student=student)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enrollment'] = self.object
        context['course'] = self.object.course
        return context
    
    def form_valid(self, form):
        enrollment = form.save()
        
        # Create history record
        user_name = self.request.user.get_full_name() or self.request.user.username
        EnrollmentHistory.objects.create(
            enrollment=enrollment,
            old_status=enrollment.status,
            new_status=enrollment.status,
            changed_by=user_name,
            reason='فیش واریزی آپلود شد'
        )
        
        logger.info(f"Payment receipt uploaded for enrollment: {enrollment}")
        
        messages.success(
            self.request,
            'فیش واریزی شما با موفقیت آپلود شد. پس از بررسی توسط مدیریت، وضعیت ثبت‌نام شما به‌روزرسانی خواهد شد.',
            extra_tags='enrollment'
        )
        
        return redirect('enrollment:my-enrollments')
    
    def get_success_url(self):
        return reverse('enrollment:my-enrollments')


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
        user_name = request.user.get_full_name() or request.user.username
        if enrollment.cancel_enrollment(reason=reason, cancelled_by=user_name):
            
            # Create history record
            EnrollmentHistory.objects.create(
                enrollment=enrollment,
                old_status='confirmed',
                new_status='cancelled',
                changed_by=user_name,
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

