"""
Unit tests for enrollment models
"""
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from enrollment.models import Enrollment, EnrollmentPayment
from account.models import Student
from course.models import Course
from django.contrib.auth import get_user_model

User = get_user_model()


class TestEnrollmentModel(TestCase):
    """Test cases for the Enrollment model"""
    
    def setUp(self):
        # Create student
        self.student_user = User.objects.create_user(
            email='student@example.com',
            password='pass123',
            user_type='student'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            phone_number='09123456789',
            age=25
        )
        
        # Create teacher and course
        self.teacher_user = User.objects.create_user(
            email='teacher@example.com',
            password='pass123',
            user_type='teacher'
        )
        from account.models import Teacher
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            full_name='Test Teacher'
        )
        
        from course.models import Category
        self.category = Category.objects.create(
            name='Test Category',
            language='english'
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            teacher=self.teacher,
            category=self.category,
            level='beginner',
            price=1000000,
            duration_weeks=8,
            capacity=20
        )
        
        self.enrollment_data = {
            'student': self.student,
            'course': self.course,
            'status': 'pending',
            'payment_status': 'unpaid'
        }
    
    def test_create_enrollment(self):
        """Test creating an enrollment"""
        enrollment = Enrollment.objects.create(**self.enrollment_data)
        self.assertEqual(enrollment.student, self.student)
        self.assertEqual(enrollment.course, self.course)
        self.assertEqual(enrollment.status, 'pending')
        self.assertEqual(enrollment.payment_status, 'unpaid')
        self.assertIsNotNone(enrollment.enrolled_at)
        self.assertIsNone(enrollment.confirmed_at)
        self.assertIsNone(enrollment.cancelled_at)
    
    def test_enrollment_string_representation(self):
        """Test enrollment string representation"""
        enrollment = Enrollment.objects.create(**self.enrollment_data)
        expected = f'{self.student.user.get_full_name()} - {self.course.title}'
        self.assertEqual(str(enrollment), expected)
    
    def test_enrollment_status_choices(self):
        """Test enrollment status choices"""
        valid_statuses = ['pending', 'confirmed', 'cancelled', 'completed', 'expired']
        for status in valid_statuses:
            enrollment_data = self.enrollment_data.copy()
            enrollment_data['status'] = status
            enrollment = Enrollment.objects.create(**enrollment_data)
            self.assertEqual(enrollment.status, status)
    
    def test_payment_status_choices(self):
        """Test payment status choices"""
        valid_statuses = ['unpaid', 'paid', 'partial', 'refunded']
        for status in valid_statuses:
            enrollment_data = self.enrollment_data.copy()
            enrollment_data['payment_status'] = status
            enrollment = Enrollment.objects.create(**enrollment_data)
            self.assertEqual(enrollment.payment_status, status)
    
    def test_confirm_enrollment(self):
        """Test confirming an enrollment"""
        enrollment = Enrollment.objects.create(**self.enrollment_data)
        
        # Confirm enrollment
        enrollment.confirm()
        
        self.assertEqual(enrollment.status, 'confirmed')
        self.assertIsNotNone(enrollment.confirmed_at)
    
    def test_cancel_enrollment(self):
        """Test cancelling an enrollment"""
        enrollment = Enrollment.objects.create(**self.enrollment_data)
        
        # Cancel enrollment
        enrollment.cancel('Student requested cancellation')
        
        self.assertEqual(enrollment.status, 'cancelled')
        self.assertIsNotNone(enrollment.cancelled_at)
        self.assertEqual(enrollment.note, 'Student requested cancellation')
    
    def test_complete_enrollment(self):
        """Test completing an enrollment"""
        enrollment = Enrollment.objects.create(**self.enrollment_data)
        enrollment.status = 'confirmed'
        enrollment.save()
        
        # Complete enrollment
        enrollment.complete()
        
        self.assertEqual(enrollment.status, 'completed')
    
    def test_enrollment_is_active(self):
        """Test enrollment is_active property"""
        enrollment = Enrollment.objects.create(**self.enrollment_data)
        
        # Pending enrollment should not be active
        enrollment.status = 'pending'
        enrollment.save()
        self.assertFalse(enrollment.is_active())
        
        # Confirmed enrollment should be active
        enrollment.status = 'confirmed'
        enrollment.save()
        self.assertTrue(enrollment.is_active())
        
        # Cancelled enrollment should not be active
        enrollment.status = 'cancelled'
        enrollment.save()
        self.assertFalse(enrollment.is_active())
    
    def test_enrollment_can_be_cancelled(self):
        """Test enrollment can_be_cancelled property"""
        enrollment = Enrollment.objects.create(**self.enrollment_data)
        
        # Pending enrollment can be cancelled
        enrollment.status = 'pending'
        enrollment.save()
        self.assertTrue(enrollment.can_be_cancelled())
        
        # Confirmed enrollment can be cancelled
        enrollment.status = 'confirmed'
        enrollment.save()
        self.assertTrue(enrollment.can_be_cancelled())
        
        # Completed enrollment cannot be cancelled
        enrollment.status = 'completed'
        enrollment.save()
        self.assertFalse(enrollment.can_be_cancelled())
        
        # Already cancelled enrollment cannot be cancelled
        enrollment.status = 'cancelled'
        enrollment.save()
        self.assertFalse(enrollment.can_be_cancelled())
    
    def test_enrollment_unique_together(self):
        """Test student-course unique constraint"""
        # Create first enrollment
        Enrollment.objects.create(**self.enrollment_data)
        
        # Try to create duplicate enrollment
        with self.assertRaises(Exception):  # IntegrityError
            Enrollment.objects.create(**self.enrollment_data)
    
    def test_enrollment_ordering(self):
        """Test enrollment ordering"""
        # Create multiple enrollments
        enrollment1 = Enrollment.objects.create(**self.enrollment_data)
        
        # Create another course and enrollment
        course2 = Course.objects.create(
            title='Test Course 2',
            teacher=self.teacher,
            category=self.category,
            level='intermediate',
            price=1500000,
            duration_weeks=10,
            capacity=15
        )
        enrollment_data2 = self.enrollment_data.copy()
        enrollment_data2['course'] = course2
        enrollment2 = Enrollment.objects.create(**enrollment_data2)
        
        # Check ordering (should be by -enrolled_at)
        enrollments = list(Enrollment.objects.all())
        self.assertEqual(enrollments[0], enrollment2)  # Most recent first
        self.assertEqual(enrollments[1], enrollment1)
    
    def test_enrollment_expiry(self):
        """Test enrollment expiry logic"""
        enrollment = Enrollment.objects.create(**self.enrollment_data)
        
        # Set enrolled_at to past date
        past_date = timezone.now() - timedelta(days=8)
        enrollment.enrolled_at = past_date
        enrollment.save()
        
        # Check if expired (assuming 7-day expiry for pending enrollments)
        self.assertTrue(enrollment.is_expired())
        
        # Confirmed enrollment should not expire based on time
        enrollment.status = 'confirmed'
        enrollment.save()
        self.assertFalse(enrollment.is_expired())


class TestEnrollmentPaymentModel(TestCase):
    """Test cases for the EnrollmentPayment model"""
    
    def setUp(self):
        # Create basic enrollment (reuse setup from TestEnrollmentModel)
        self.student_user = User.objects.create_user(
            email='student@example.com',
            password='pass123',
            user_type='student'
        )
        self.student = Student.objects.create(
            user=self.student_user,
            phone_number='09123456789',
            age=25
        )
        
        self.teacher_user = User.objects.create_user(
            email='teacher@example.com',
            password='pass123',
            user_type='teacher'
        )
        from account.models import Teacher
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            full_name='Test Teacher'
        )
        
        from course.models import Category
        self.category = Category.objects.create(
            name='Test Category',
            language='english'
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            teacher=self.teacher,
            category=self.category,
            level='beginner',
            price=1000000,
            duration_weeks=8,
            capacity=20
        )
        
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            course=self.course
        )
        
        self.payment_data = {
            'enrollment': self.enrollment,
            'amount': 1000000,
            'payment_method': 'online',
            'transaction_id': 'TXN123456789'
        }
    
    def test_create_payment(self):
        """Test creating a payment"""
        payment = EnrollmentPayment.objects.create(**self.payment_data)
        self.assertEqual(payment.enrollment, self.enrollment)
        self.assertEqual(payment.amount, 1000000)
        self.assertEqual(payment.payment_method, 'online')
        self.assertEqual(payment.transaction_id, 'TXN123456789')
        self.assertEqual(payment.status, 'pending')  # Default status
        self.assertIsNotNone(payment.created_at)
    
    def test_payment_string_representation(self):
        """Test payment string representation"""
        payment = EnrollmentPayment.objects.create(**self.payment_data)
        expected = f'Payment {payment.transaction_id} - {payment.amount}'
        self.assertEqual(str(payment), expected)
    
    def test_payment_status_choices(self):
        """Test payment status choices"""
        valid_statuses = ['pending', 'completed', 'failed', 'cancelled', 'refunded']
        for status in valid_statuses:
            payment_data = self.payment_data.copy()
            payment_data['transaction_id'] = f'TXN{status}123'
            payment = EnrollmentPayment.objects.create(**payment_data)
            payment.status = status
            payment.save()
            self.assertEqual(payment.status, status)
    
    def test_payment_method_choices(self):
        """Test payment method choices"""
        valid_methods = ['online', 'bank_transfer', 'cash', 'installment']
        for method in valid_methods:
            payment_data = self.payment_data.copy()
            payment_data['payment_method'] = method
            payment_data['transaction_id'] = f'TXN{method}123'
            payment = EnrollmentPayment.objects.create(**payment_data)
            self.assertEqual(payment.payment_method, method)
    
    def test_payment_confirm(self):
        """Test confirming a payment"""
        payment = EnrollmentPayment.objects.create(**self.payment_data)
        
        # Confirm payment
        payment.confirm()
        
        self.assertEqual(payment.status, 'completed')
        self.assertIsNotNone(payment.confirmed_at)
    
    def test_payment_fail(self):
        """Test failing a payment"""
        payment = EnrollmentPayment.objects.create(**self.payment_data)
        
        # Fail payment
        payment.fail('Payment gateway error')
        
        self.assertEqual(payment.status, 'failed')
        self.assertEqual(payment.failure_reason, 'Payment gateway error')
    
    def test_payment_refund(self):
        """Test refunding a payment"""
        payment = EnrollmentPayment.objects.create(**self.payment_data)
        payment.status = 'completed'
        payment.save()
        
        # Refund payment
        payment.refund('Student cancellation')
        
        self.assertEqual(payment.status, 'refunded')
        self.assertEqual(payment.refund_reason, 'Student cancellation')
        self.assertIsNotNone(payment.refunded_at)


@pytest.mark.django_db
class TestEnrollmentModelPytest:
    """Pytest-style tests for Enrollment model"""
    
    def test_create_enrollment_with_fixtures(self, enrollment):
        """Test creating enrollment with fixtures"""
        assert enrollment.status == 'confirmed'
        assert enrollment.payment_status == 'paid'
        assert enrollment.is_active()
    
    def test_enrollment_relationships(self, enrollment, student_profile, course):
        """Test enrollment relationships"""
        assert enrollment.student == student_profile
        assert enrollment.course == course
        assert enrollment in student_profile.enrollments.all()
        assert enrollment in course.enrollments.all()
    
    def test_enrollment_workflow(self, student_profile, course):
        """Test complete enrollment workflow"""
        # Create pending enrollment
        enrollment = Enrollment.objects.create(
            student=student_profile,
            course=course,
            status='pending',
            payment_status='unpaid'
        )
        
        assert not enrollment.is_active()
        assert enrollment.can_be_cancelled()
        
        # Confirm enrollment
        enrollment.confirm()
        assert enrollment.status == 'confirmed'
        assert enrollment.is_active()
        
        # Complete enrollment
        enrollment.complete()
        assert enrollment.status == 'completed'
        assert not enrollment.can_be_cancelled() 