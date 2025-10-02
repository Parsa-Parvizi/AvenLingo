"""
Business logic services for user management and teacher applications.
Following Domain-Driven Design principles and separation of concerns.
"""

import logging
from typing import Optional, Dict, Any
from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import User, Student, Teacher, TeacherApplication


logger = logging.getLogger(__name__)


class UserRegistrationService:
    """Service for handling user registration workflow"""
    
    @staticmethod
    def register_student(email: str, password: str, first_name: str, 
                        last_name: str, **profile_data) -> User:
        """
        Register a new student with email verification workflow
        
        Args:
            email: User email
            password: User password
            first_name: User first name
            last_name: User last name
            **profile_data: Additional student profile data
            
        Returns:
            User: Created user instance
            
        Raises:
            ValidationError: If email already exists or validation fails
        """
        try:
            with transaction.atomic():
                # Check if email already exists
                if User.objects.filter(email=email).exists():
                    raise ValidationError("این ایمیل قبلاً ثبت شده است")
                
                # Create user
                user = User.objects.create_student(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Create student profile
                student = Student.create_for_user(user, **profile_data)
                
                # Generate and send verification email
                token = user.generate_email_verification_token()
                EmailService.send_student_verification_email(user, token)
                
                logger.info(f"Student registered successfully: {email}")
                return user
                
        except Exception as e:
            logger.error(f"Error registering student {email}: {str(e)}")
            raise
    
    @staticmethod
    def register_teacher_from_application(application: TeacherApplication, 
                                        password: str, **profile_data) -> User:
        """
        Register a new teacher from approved application
        
        Args:
            application: Approved TeacherApplication instance
            password: User password
            **profile_data: Additional teacher profile data
            
        Returns:
            User: Created user instance
            
        Raises:
            ValidationError: If application is not valid for teacher creation
        """
        try:
            with transaction.atomic():
                if not application.can_create_teacher_account():
                    raise ValidationError("این درخواست برای ایجاد حساب معلم معتبر نیست")
                
                # Check if user already exists
                if User.objects.filter(email=application.email).exists():
                    raise ValidationError("حساب کاربری با این ایمیل قبلاً وجود دارد")
                
                # Create teacher user
                user = User.objects.create_user(
                    email=application.email,
                    password=password,
                    first_name=application.first_name,
                    last_name=application.last_name,
                    user_type=User.UserType.TEACHER,
                    is_email_verified=True  # Teachers don't need email verification
                )
                
                # Activate user immediately
                user.activate()
                
                # Create teacher profile
                teacher = Teacher.create_from_application(
                    application=application,
                    user=user,
                    **profile_data
                )
                
                # Send welcome email
                EmailService.send_teacher_welcome_email(user)
                
                logger.info(f"Teacher registered successfully: {application.email}")
                return user
                
        except Exception as e:
            logger.error(f"Error registering teacher from application {application.id}: {str(e)}")
            raise
    
    @staticmethod
    def verify_student_email(user_id: str, token: str) -> bool:
        """
        Verify student email with token
        
        Args:
            user_id: User ID
            token: Verification token
            
        Returns:
            bool: True if verification successful
        """
        try:
            user = User.objects.get(id=user_id)
            
            if not user.can_verify_email():
                logger.warning(f"Email verification expired for user {user_id}")
                return False
            
            if user.verify_email(token):
                logger.info(f"Email verified successfully for user {user_id}")
                return True
            
            logger.warning(f"Invalid verification token for user {user_id}")
            return False
            
        except User.DoesNotExist:
            logger.error(f"User not found for email verification: {user_id}")
            return False
        except Exception as e:
            logger.error(f"Error verifying email for user {user_id}: {str(e)}")
            return False


class TeacherApplicationService:
    """Service for handling teacher application workflow"""
    
    @staticmethod
    def submit_application(first_name: str, last_name: str, email: str,
                          phone_number: str, education: str, experience: str,
                          specialties: str, motivation: str, **kwargs) -> TeacherApplication:
        """
        Submit a new teacher application
        
        Args:
            Personal and professional information
            
        Returns:
            TeacherApplication: Created application instance
            
        Raises:
            ValidationError: If email already has an application
        """
        try:
            # Check if application already exists for this email
            if TeacherApplication.objects.for_email(email).exists():
                raise ValidationError("درخواست همکاری با این ایمیل قبلاً ثبت شده است")
            
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                raise ValidationError("کاربری با این ایمیل قبلاً ثبت شده است")
            
            application = TeacherApplication.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                education=education,
                experience=experience,
                specialties=specialties,
                motivation=motivation,
                **kwargs
            )
            
            # Notify admin about new application
            EmailService.send_admin_new_application_notification(application)
            
            logger.info(f"Teacher application submitted: {email}")
            return application
            
        except Exception as e:
            logger.error(f"Error submitting teacher application for {email}: {str(e)}")
            raise
    
    @staticmethod
    def approve_application(application: TeacherApplication, 
                          reviewed_by: User, admin_notes: str = "") -> None:
        """
        Approve a teacher application
        
        Args:
            application: TeacherApplication to approve
            reviewed_by: Admin user who reviewed the application
            admin_notes: Optional admin notes
        """
        try:
            with transaction.atomic():
                application.mark_as_accepted(reviewed_by, admin_notes)
                
                # Send approval email with registration link
                EmailService.send_teacher_approval_email(application)
                
                logger.info(f"Teacher application approved: {application.email} by {reviewed_by.email}")
                
        except Exception as e:
            logger.error(f"Error approving application {application.id}: {str(e)}")
            raise
    
    @staticmethod
    def reject_application(application: TeacherApplication, 
                         reviewed_by: User, admin_notes: str = "") -> None:
        """
        Reject a teacher application
        
        Args:
            application: TeacherApplication to reject
            reviewed_by: Admin user who reviewed the application
            admin_notes: Optional admin notes
        """
        try:
            with transaction.atomic():
                application.mark_as_rejected(reviewed_by, admin_notes)
                
                # Send rejection email
                EmailService.send_teacher_rejection_email(application)
                
                logger.info(f"Teacher application rejected: {application.email} by {reviewed_by.email}")
                
        except Exception as e:
            logger.error(f"Error rejecting application {application.id}: {str(e)}")
            raise
    
    @staticmethod
    def check_registration_eligibility(email: str) -> Optional[TeacherApplication]:
        """
        Check if email is eligible for teacher registration
        
        Args:
            email: Email to check
            
        Returns:
            TeacherApplication or None if not eligible
        """
        try:
            application = TeacherApplication.objects.get(
                email=email, 
                status=TeacherApplication.Status.ACCEPTED
            )
            
            if application.can_create_teacher_account():
                return application
            
            return None
            
        except TeacherApplication.DoesNotExist:
            return None


class EmailService:
    """Service for handling email notifications"""
    
    @staticmethod
    def send_student_verification_email(user: User, token: str) -> bool:
        """Send verification email to student"""
        try:
            # This would use the site domain from settings or request
            verification_url = f"{settings.SITE_URL}/auth/verify-email/{user.id}/{token}/"
            
            context = {
                'user': user,
                'verification_url': verification_url,
                'site_name': getattr(settings, 'SITE_NAME', 'آکادمی زبان مبینا')
            }
            
            subject = 'تایید ایمیل - آکادمی زبان مبینا'
            message = render_to_string('account/emails/student_verification.html', context)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=message
            )
            
            logger.info(f"Verification email sent to: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending verification email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_teacher_approval_email(application: TeacherApplication) -> bool:
        """Send approval email to teacher with registration link"""
        try:
            registration_url = f"{settings.SITE_URL}/auth/register/teacher/{application.email}/"
            
            context = {
                'application': application,
                'registration_url': registration_url,
                'expiry_date': application.expires_at,
                'site_name': getattr(settings, 'SITE_NAME', 'آکادمی زبان مبینا')
            }
            
            subject = 'تایید درخواست همکاری - آکادمی زبان مبینا'
            message = render_to_string('account/emails/teacher_approval.html', context)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.email],
                html_message=message
            )
            
            logger.info(f"Approval email sent to: {application.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending approval email to {application.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_teacher_rejection_email(application: TeacherApplication) -> bool:
        """Send rejection email to teacher"""
        try:
            context = {
                'application': application,
                'admin_notes': application.admin_notes,
                'site_name': getattr(settings, 'SITE_NAME', 'آکادمی زبان مبینا')
            }
            
            subject = 'نتیجه درخواست همکاری - آکادمی زبان مبینا'
            message = render_to_string('account/emails/teacher_rejection.html', context)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.email],
                html_message=message
            )
            
            logger.info(f"Rejection email sent to: {application.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending rejection email to {application.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_teacher_welcome_email(user: User) -> bool:
        """Send welcome email to new teacher"""
        try:
            context = {
                'user': user,
                'dashboard_url': f"{settings.SITE_URL}/auth/dashboard/",
                'site_name': getattr(settings, 'SITE_NAME', 'آکادمی زبان مبینا')
            }
            
            subject = 'خوش آمدید - آکادمی زبان مبینا'
            message = render_to_string('account/emails/teacher_welcome.html', context)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=message
            )
            
            logger.info(f"Welcome email sent to: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_admin_new_application_notification(application: TeacherApplication) -> bool:
        """Send notification to admin about new teacher application"""
        try:
            admin_emails = User.objects.filter(
                is_staff=True, 
                is_active=True
            ).values_list('email', flat=True)
            
            if not admin_emails:
                logger.warning("No admin emails found for notification")
                return False
            
            context = {
                'application': application,
                'admin_url': f"{settings.SITE_URL}/admin/account/teacherapplication/{application.id}/",
                'site_name': getattr(settings, 'SITE_NAME', 'آکادمی زبان مبینا')
            }
            
            subject = 'درخواست همکاری جدید - آکادمی زبان مبینا'
            message = render_to_string('account/emails/admin_new_application.html', context)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(admin_emails),
                html_message=message
            )
            
            logger.info(f"Admin notification sent for application: {application.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending admin notification for application {application.id}: {str(e)}")
            return False


class UserProfileService:
    """Service for handling user profile operations"""
    
    @staticmethod
    def update_student_profile(student: Student, **data) -> Student:
        """Update student profile with validation"""
        try:
            with transaction.atomic():
                # Update user fields if provided
                user_fields = ['first_name', 'last_name']
                user_data = {k: v for k, v in data.items() if k in user_fields}
                if user_data:
                    for field, value in user_data.items():
                        setattr(student.user, field, value)
                    student.user.save(update_fields=user_fields)
                
                # Update student fields
                student_fields = [
                    'national_id', 'phone_number', 'date_of_birth', 
                    'address', 'english_level', 'goals'
                ]
                student_data = {k: v for k, v in data.items() if k in student_fields}
                if student_data:
                    for field, value in student_data.items():
                        setattr(student, field, value)
                    student.save(update_fields=list(student_data.keys()))
                
                logger.info(f"Student profile updated: {student.user.email}")
                return student
                
        except Exception as e:
            logger.error(f"Error updating student profile {student.id}: {str(e)}")
            raise
    
    @staticmethod
    def update_teacher_profile(teacher: Teacher, **data) -> Teacher:
        """Update teacher profile with validation"""
        try:
            with transaction.atomic():
                # Update user fields if provided
                user_fields = ['first_name', 'last_name']
                user_data = {k: v for k, v in data.items() if k in user_fields}
                if user_data:
                    for field, value in user_data.items():
                        setattr(teacher.user, field, value)
                    teacher.user.save(update_fields=user_fields)
                
                # Update teacher fields
                teacher_fields = [
                    'bio', 'specialties', 'hourly_rate', 'telegram_username'
                ]
                teacher_data = {k: v for k, v in data.items() if k in teacher_fields}
                if teacher_data:
                    for field, value in teacher_data.items():
                        setattr(teacher, field, value)
                    teacher.save(update_fields=list(teacher_data.keys()))
                
                logger.info(f"Teacher profile updated: {teacher.user.email}")
                return teacher
                
        except Exception as e:
            logger.error(f"Error updating teacher profile {teacher.id}: {str(e)}")
            raise 