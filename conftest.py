"""
Global pytest configuration and fixtures for the project
"""
import pytest
import os
import django
from django.conf import settings
from django.test import TestCase
from django.contrib.auth import get_user_model
from account.models import Student
from teacher.models import Teacher
from course.models import Course, Category
from enrollment.models import Enrollment

# Configure Django settings for pytest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EnglishTeacher.test_settings')
django.setup()

User = get_user_model()


@pytest.fixture(scope='session')
def django_db_setup():
    """Set up the test database"""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 20,
        }
    }


@pytest.fixture
def user_factory():
    """Factory for creating users"""
    def create_user(email='test@example.com', user_type='student', **kwargs):
        return User.objects.create_user(
            email=email,
            password='testpass123',
            user_type=user_type,
            is_active=True,
            **kwargs
        )
    return create_user


@pytest.fixture
def student_user(user_factory):
    """Create a student user"""
    return user_factory(email='student@example.com', user_type='student')


@pytest.fixture
def teacher_user(user_factory):
    """Create a teacher user"""
    return user_factory(email='teacher@example.com', user_type='teacher')


@pytest.fixture
def admin_user(user_factory):
    """Create an admin user"""
    return user_factory(
        email='admin@example.com', 
        user_type='admin',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def student_profile(student_user):
    """Create a student profile"""
    return Student.objects.create(
        user=student_user,
        phone_number='09123456789',
        age=25,
        education_level='bachelor',
        learning_goal='business'
    )


@pytest.fixture
def teacher_profile(teacher_user):
    """Create a teacher profile"""
    return Teacher.objects.create(
        user=teacher_user,
        full_name='Test Teacher',
        bio='Experienced English teacher',
        expertise='IELTS Preparation',
        phone_number='09123456789',
        registration_status='approved'
    )


@pytest.fixture
def course_category():
    """Create a course category"""
    return Category.objects.create(
        name='General English',
        slug='general-english',
        description='General English courses',
        language='english',
        is_active=True
    )


@pytest.fixture
def course(teacher_profile, course_category):
    """Create a course"""
    return Course.objects.create(
        title='English Conversation',
        description='Learn English conversation skills',
        teacher=teacher_profile,
        category=course_category,
        level='beginner',
        price=1000000,
        duration_weeks=8,
        capacity=20,
        is_active=True
    )


@pytest.fixture
def enrollment(student_profile, course):
    """Create an enrollment"""
    return Enrollment.objects.create(
        student=student_profile,
        course=course,
        status='confirmed',
        payment_status='paid'
    )


@pytest.fixture
def client():
    """Django test client"""
    from django.test import Client
    return Client()


@pytest.fixture
def authenticated_client(client, student_user):
    """Authenticated client with student user"""
    client.force_login(student_user)
    return client


@pytest.fixture
def teacher_client(client, teacher_user):
    """Authenticated client with teacher user"""
    client.force_login(teacher_user)
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Authenticated client with admin user"""
    client.force_login(admin_user)
    return client 