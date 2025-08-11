"""
Unit tests for account models
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from account.models import Student, UserProfile, SecurityQuestion
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class TestUserModel(TestCase):
    """Test cases for the custom User model"""
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'user_type': 'student'
        }
    
    def test_create_user_with_email(self):
        """Test creating a user with email"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.user_type, 'student')  # Default
        
    def test_create_user_without_email(self):
        """Test creating user without email raises ValueError"""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='testpass123')
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        superuser = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
        self.assertTrue(superuser.is_active)
        
    def test_superuser_must_have_is_staff_true(self):
        """Test superuser creation with is_staff=False raises ValueError"""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass123',
                is_staff=False
            )
    
    def test_superuser_must_have_is_superuser_true(self):
        """Test superuser creation with is_superuser=False raises ValueError"""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com',
                password='adminpass123',
                is_superuser=False
            )
    
    def test_user_string_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')
    
    def test_get_full_name(self):
        """Test get_full_name method"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), 'John Doe')
        
        # Test with missing first_name
        user.first_name = ''
        self.assertEqual(user.get_full_name(), 'Doe')
        
        # Test with missing both names
        user.last_name = ''
        self.assertEqual(user.get_full_name(), 'test@example.com')
    
    def test_get_short_name(self):
        """Test get_short_name method"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_short_name(), 'John')
        
        # Test with missing first_name
        user.first_name = ''
        self.assertEqual(user.get_short_name(), 'test@example.com')
    
    def test_email_uniqueness(self):
        """Test email uniqueness constraint"""
        User.objects.create_user(email='test@example.com', password='pass123')
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email='test@example.com', password='pass456')
    
    def test_user_type_choices(self):
        """Test user type choices"""
        valid_types = ['student', 'teacher', 'admin']
        for user_type in valid_types:
            user = User.objects.create_user(
                email=f'{user_type}@example.com',
                password='pass123',
                user_type=user_type
            )
            self.assertEqual(user.user_type, user_type)
    
    def test_email_normalization(self):
        """Test email normalization"""
        user = User.objects.create_user(
            email='Test@EXAMPLE.COM',
            password='pass123'
        )
        self.assertEqual(user.email, 'Test@example.com')


class TestStudentModel(TestCase):
    """Test cases for the Student model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='student@example.com',
            password='pass123',
            user_type='student'
        )
        self.student_data = {
            'user': self.user,
            'phone_number': '09123456789',
            'age': 25,
            'education_level': 'bachelor',
            'learning_goal': 'business'
        }
    
    def test_create_student(self):
        """Test creating a student"""
        student = Student.objects.create(**self.student_data)
        self.assertEqual(student.user, self.user)
        self.assertEqual(student.phone_number, '09123456789')
        self.assertEqual(student.age, 25)
        self.assertEqual(student.education_level, 'bachelor')
        self.assertEqual(student.learning_goal, 'business')
        self.assertTrue(student.is_active)
    
    def test_student_string_representation(self):
        """Test student string representation"""
        student = Student.objects.create(**self.student_data)
        self.assertEqual(str(student), self.user.get_full_name() or self.user.email)
    
    def test_student_age_validation(self):
        """Test student age validation"""
        # Test valid age
        student = Student(**self.student_data)
        student.full_clean()  # Should not raise
        
        # Test invalid age (too young)
        student.age = 5
        with self.assertRaises(ValidationError):
            student.full_clean()
        
        # Test invalid age (too old)
        student.age = 150
        with self.assertRaises(ValidationError):
            student.full_clean()
    
    def test_phone_number_validation(self):
        """Test phone number validation"""
        # Test valid Iranian phone number
        self.student_data['phone_number'] = '09123456789'
        student = Student(**self.student_data)
        student.full_clean()  # Should not raise
        
        # Test invalid phone number
        self.student_data['phone_number'] = '123'
        student = Student(**self.student_data)
        with self.assertRaises(ValidationError):
            student.full_clean()
    
    def test_education_level_choices(self):
        """Test education level choices"""
        valid_levels = ['high_school', 'diploma', 'bachelor', 'master', 'phd', 'other']
        for level in valid_levels:
            self.student_data['education_level'] = level
            student = Student.objects.create(**self.student_data)
            self.assertEqual(student.education_level, level)
    
    def test_learning_goal_choices(self):
        """Test learning goal choices"""
        valid_goals = ['academic', 'business', 'travel', 'immigration', 'personal', 'exam_prep']
        for goal in valid_goals:
            self.student_data['learning_goal'] = goal
            student = Student.objects.create(**self.student_data)
            self.assertEqual(student.learning_goal, goal)


class TestUserProfileModel(TestCase):
    """Test cases for the UserProfile model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='profile@example.com',
            password='pass123'
        )
    
    def test_create_user_profile(self):
        """Test creating a user profile"""
        profile = UserProfile.objects.create(
            user=self.user,
            bio='Test bio',
            birth_date=datetime(1990, 1, 1).date(),
            location='Tehran, Iran'
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.bio, 'Test bio')
        self.assertEqual(profile.location, 'Tehran, Iran')
    
    def test_profile_string_representation(self):
        """Test profile string representation"""
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(str(profile), f'{self.user.email} Profile')
    
    def test_avatar_upload_path(self):
        """Test avatar upload path"""
        profile = UserProfile.objects.create(user=self.user)
        # This would test the upload path if we had actual file upload
        # For now, we'll just check the field exists
        self.assertTrue(hasattr(profile, 'avatar'))


class TestSecurityQuestionModel(TestCase):
    """Test cases for the SecurityQuestion model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='security@example.com',
            password='pass123'
        )
    
    def test_create_security_question(self):
        """Test creating a security question"""
        question = SecurityQuestion.objects.create(
            user=self.user,
            question='What is your mother\'s maiden name?',
            answer='Smith'
        )
        self.assertEqual(question.user, self.user)
        self.assertEqual(question.question, 'What is your mother\'s maiden name?')
        # Answer should be hashed
        self.assertNotEqual(question.answer, 'Smith')
    
    def test_check_answer(self):
        """Test checking security question answer"""
        question = SecurityQuestion.objects.create(
            user=self.user,
            question='What is your mother\'s maiden name?',
            answer='Smith'
        )
        # Test correct answer
        self.assertTrue(question.check_answer('Smith'))
        # Test incorrect answer
        self.assertFalse(question.check_answer('Jones'))
    
    def test_security_question_string_representation(self):
        """Test security question string representation"""
        question = SecurityQuestion.objects.create(
            user=self.user,
            question='What is your mother\'s maiden name?',
            answer='Smith'
        )
        expected = f'{self.user.email} - What is your mother\'s maiden name?'
        self.assertEqual(str(question), expected)


@pytest.mark.django_db
class TestUserModelPytest:
    """Pytest-style tests for User model"""
    
    def test_create_user_with_factory(self, user_factory):
        """Test creating user with factory"""
        user = user_factory(email='pytest@example.com')
        assert user.email == 'pytest@example.com'
        assert user.user_type == 'student'
        assert user.is_active
    
    def test_user_permissions(self, admin_user, teacher_user, student_user):
        """Test user permissions based on type"""
        assert admin_user.is_superuser
        assert admin_user.is_staff
        
        assert not teacher_user.is_superuser
        assert not teacher_user.is_staff
        
        assert not student_user.is_superuser
        assert not student_user.is_staff
    
    def test_user_profile_creation(self, student_profile):
        """Test student profile creation"""
        assert student_profile.user.user_type == 'student'
        assert student_profile.phone_number == '09123456789'
        assert student_profile.age == 25 