"""
تست‌های همگام‌سازی ثبت‌نام و پرداخت
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from account.models import User, Student, Teacher
from course.models import Course, Category
from enrollment.models import Enrollment


class EnrollmentPaymentSyncTests(TestCase):
    """تست همگام‌سازی وضعیت ثبت‌نام و پرداخت"""
    
    def setUp(self):
        """راه‌اندازی اولیه"""
        # ایجاد دسته‌بندی
        self.category = Category.objects.create(
            title="تست",
            slug="test"
        )
        
        # ایجاد معلم
        self.teacher_user = User.objects.create_user(
            email='teacher@test.com',
            password='test123',
            first_name='معلم',
            last_name='تستی',
            user_type='teacher'
        )
        self.teacher = Teacher.objects.create(user=self.teacher_user)
        
        # ایجاد دانش‌آموز
        self.student_user = User.objects.create_user(
            email='student@test.com',
            password='test123',
            first_name='دانش‌آموز',
            last_name='تستی',
            user_type='student'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            date_of_birth='2000-01-01'
        )
        
        # ایجاد دوره غیر رایگان
        self.paid_course = Course.objects.create(
            title='دوره پولی',
            teacher=self.teacher,
            category=self.category,
            price=Decimal('1000000'),
            is_free=False,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30)
        )
        
        # ایجاد دوره رایگان
        self.free_course = Course.objects.create(
            title='دوره رایگان',
            teacher=self.teacher,
            category=self.category,
            price=Decimal('0'),
            is_free=True,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30)
        )
    
    def test_free_course_auto_paid(self):
        """تست: دوره رایگان خودکار payment را paid می‌کند"""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.free_course,
            status='confirmed'
        )
        
        self.assertEqual(enrollment.payment_status, 'paid')
        self.assertEqual(enrollment.amount_paid, 0)
    
    def test_paid_course_cannot_confirm_without_payment(self):
        """تست: دوره پولی نمی‌تواند بدون پرداخت تایید شود"""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.paid_course,
            status='confirmed',
            payment_status='unpaid'
        )
        
        # باید به pending برگردانده شود
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, 'pending')
        self.assertIsNone(enrollment.confirmed_at)
    
    def test_paid_course_can_confirm_with_full_payment(self):
        """تست: دوره پولی با پرداخت کامل قابل تایید است"""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.paid_course,
            status='pending',
            payment_status='paid',
            amount_paid=self.paid_course.price
        )
        
        # باید خودکار confirmed شود
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, 'confirmed')
        self.assertIsNotNone(enrollment.confirmed_at)
    
    def test_paid_course_can_confirm_with_partial_payment(self):
        """تست: دوره پولی با پرداخت جزئی قابل تایید است"""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.paid_course,
            status='pending',
            payment_status='partial',
            amount_paid=self.paid_course.price / 2
        )
        
        # باید خودکار confirmed شود
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, 'confirmed')
        self.assertIsNotNone(enrollment.confirmed_at)
    
    def test_confirm_enrollment_method_paid_course(self):
        """تست: متد confirm_enrollment برای دوره پولی"""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.paid_course,
            status='pending',
            payment_status='unpaid'
        )
        
        # تلاش برای تایید بدون پرداخت
        success, message = enrollment.confirm_enrollment()
        self.assertFalse(success)
        self.assertIn('پرداخت', message)
        
        # پرداخت و سپس تایید
        enrollment.payment_status = 'paid'
        enrollment.amount_paid = self.paid_course.price
        enrollment.save()
        
        success, message = enrollment.confirm_enrollment()
        self.assertTrue(success)
        self.assertEqual(enrollment.status, 'confirmed')
    
    def test_confirm_enrollment_method_free_course(self):
        """تست: متد confirm_enrollment برای دوره رایگان"""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.free_course,
            status='pending'
        )
        
        success, message = enrollment.confirm_enrollment()
        self.assertTrue(success)
        self.assertEqual(enrollment.status, 'confirmed')
        self.assertEqual(enrollment.payment_status, 'paid')
        self.assertEqual(enrollment.amount_paid, 0)
    
    def test_confirm_payment_method(self):
        """تست: متد confirm_payment"""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.paid_course,
            status='pending',
            payment_status='unpaid'
        )
        
        # تایید پرداخت
        success, message = enrollment.confirm_payment(
            amount=self.paid_course.price
        )
        
        self.assertTrue(success)
        self.assertEqual(enrollment.payment_status, 'paid')
        self.assertEqual(enrollment.status, 'confirmed')
        self.assertIsNotNone(enrollment.confirmed_at)
    
    def test_clean_method_validation(self):
        """تست: متد clean برای validation"""
        enrollment = Enrollment(
            student=self.student,
            course=self.paid_course,
            status='confirmed',
            payment_status='unpaid'
        )
        
        # باید ValidationError بدهد
        with self.assertRaises(ValidationError) as cm:
            enrollment.clean()
        
        errors = cm.exception.message_dict
        self.assertIn('status', errors)
        self.assertIn('payment_status', errors)
    
    def test_multiple_enrollments_sync(self):
        """تست: همگام‌سازی چند ثبت‌نام"""
        # ایجاد چند ثبت‌نام با وضعیت‌های مختلف
        enrollments = [
            Enrollment.objects.create(
                student=self.student,
                course=self.paid_course,
                status='confirmed',
                payment_status='unpaid'
            ),
            Enrollment.objects.create(
                student=self.student,
                course=self.free_course,
                status='confirmed',
                payment_status='unpaid'
            ),
        ]
        
        # دوره پولی باید به pending برگردد
        enrollments[0].refresh_from_db()
        self.assertEqual(enrollments[0].status, 'pending')
        
        # دوره رایگان باید paid شود
        enrollments[1].refresh_from_db()
        self.assertEqual(enrollments[1].payment_status, 'paid')


class EnrollmentPaymentEdgeCaseTests(TestCase):
    """تست موارد خاص و لبه‌ای"""
    
    def setUp(self):
        """راه‌اندازی اولیه"""
        self.category = Category.objects.create(title="تست", slug="test")
        
        teacher_user = User.objects.create_user(
            email='teacher2@test.com',
            password='test123',
            first_name='معلم',
            last_name='دوم',
            user_type='teacher'
        )
        self.teacher = Teacher.objects.create(user=teacher_user)
        
        student_user = User.objects.create_user(
            email='student2@test.com',
            password='test123',
            first_name='دانش‌آموز',
            last_name='دوم',
            user_type='student'
        )
        self.student = Student.objects.create(
            user=student_user,
            date_of_birth='2000-01-01'
        )
        
        self.course = Course.objects.create(
            title='دوره تست',
            teacher=self.teacher,
            category=self.category,
            price=Decimal('500000'),
            is_free=False,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timezone.timedelta(days=30)
        )
    
    def test_change_payment_after_confirm(self):
        """تست: تغییر پرداخت بعد از تایید"""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
            status='pending',
            payment_status='paid',
            amount_paid=self.course.price
        )
        
        # بعد از confirmed شدن
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, 'confirmed')
        
        # تغییر payment به unpaid
        enrollment.payment_status = 'unpaid'
        enrollment.save()
        
        # باید به pending برگردد
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, 'pending')
    
    def test_refunded_payment_status(self):
        """تست: وضعیت پرداخت refunded"""
        enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course,
            status='confirmed',
            payment_status='paid',
            amount_paid=self.course.price
        )
        
        # تغییر به refunded
        enrollment.payment_status = 'refunded'
        enrollment.save()
        
        # باید به pending برگردد
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, 'pending')

