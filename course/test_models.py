"""
Unit tests for course models
"""
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from course.models import Category, Course, LANGUAGE_CHOICES
from account.models import Teacher
from django.contrib.auth import get_user_model

User = get_user_model()


class TestCategoryModel(TestCase):
    """Test cases for the Category model"""
    
    def setUp(self):
        self.category_data = {
            'name': 'General English',
            'description': 'General English courses for all levels',
            'language': 'english'
        }
    
    def test_create_category(self):
        """Test creating a category"""
        category = Category.objects.create(**self.category_data)
        self.assertEqual(category.name, 'General English')
        self.assertEqual(category.description, 'General English courses for all levels')
        self.assertEqual(category.language, 'english')
        self.assertTrue(category.is_active)
        self.assertIsNotNone(category.created_at)
    
    def test_category_string_representation(self):
        """Test category string representation"""
        category = Category.objects.create(**self.category_data)
        self.assertEqual(str(category), 'General English')
    
    def test_category_slug_auto_generation(self):
        """Test automatic slug generation"""
        category = Category.objects.create(**self.category_data)
        expected_slug = slugify(self.category_data['name'])
        self.assertEqual(category.slug, expected_slug)
    
    def test_category_custom_slug(self):
        """Test setting custom slug"""
        self.category_data['slug'] = 'custom-english-slug'
        category = Category.objects.create(**self.category_data)
        self.assertEqual(category.slug, 'custom-english-slug')
    
    def test_category_slug_uniqueness(self):
        """Test category slug uniqueness"""
        Category.objects.create(**self.category_data)
        # Try to create another category with same slug
        with self.assertRaises(Exception):  # IntegrityError
            Category.objects.create(
                name='Another English',
                slug='general-english',  # Same slug
                language='english'
            )
    
    def test_language_choices(self):
        """Test valid language choices"""
        valid_languages = [choice[0] for choice in LANGUAGE_CHOICES]
        for language in valid_languages:
            category_data = {
                'name': f'{language.title()} Category',
                'language': language
            }
            category = Category.objects.create(**category_data)
            self.assertEqual(category.language, language)
    
    def test_category_ordering(self):
        """Test category ordering"""
        # Create categories
        cat1 = Category.objects.create(name='Z Category', language='english')
        cat2 = Category.objects.create(name='A Category', language='english')
        
        # Check ordering (should be by name)
        categories = list(Category.objects.all())
        self.assertEqual(categories[0], cat2)  # A Category first
        self.assertEqual(categories[1], cat1)  # Z Category second
    
    def test_category_meta_options(self):
        """Test category meta options"""
        self.assertEqual(Category._meta.verbose_name, 'دسته‌بندی')
        self.assertEqual(Category._meta.verbose_name_plural, 'دسته‌بندی‌ها')
        self.assertEqual(Category._meta.ordering, ['name'])


class TestCourseModel(TestCase):
    """Test cases for the Course model"""
    
    def setUp(self):
        # Create user and teacher
        self.user = User.objects.create_user(
            email='teacher@example.com',
            password='pass123',
            user_type='teacher'
        )
        self.teacher = Teacher.objects.create(
            user=self.user,
            full_name='Test Teacher',
            bio='Experienced teacher',
            registration_status='approved'
        )
        
        # Create category
        self.category = Category.objects.create(
            name='English Conversation',
            language='english'
        )
        
        self.course_data = {
            'title': 'Beginner English Conversation',
            'description': 'Learn basic English conversation skills',
            'teacher': self.teacher,
            'category': self.category,
            'level': 'beginner',
            'price': 1000000,
            'duration_weeks': 8,
            'capacity': 20
        }
    
    def test_create_course(self):
        """Test creating a course"""
        course = Course.objects.create(**self.course_data)
        self.assertEqual(course.title, 'Beginner English Conversation')
        self.assertEqual(course.teacher, self.teacher)
        self.assertEqual(course.category, self.category)
        self.assertEqual(course.level, 'beginner')
        self.assertEqual(course.price, 1000000)
        self.assertEqual(course.duration_weeks, 8)
        self.assertEqual(course.capacity, 20)
        self.assertTrue(course.is_active)
        self.assertIsNotNone(course.created_at)
    
    def test_course_string_representation(self):
        """Test course string representation"""
        course = Course.objects.create(**self.course_data)
        self.assertEqual(str(course), 'Beginner English Conversation')
    
    def test_course_level_choices(self):
        """Test course level choices"""
        valid_levels = ['beginner', 'intermediate', 'advanced']
        for level in valid_levels:
            course_data = self.course_data.copy()
            course_data['title'] = f'{level.title()} Course'
            course_data['level'] = level
            course = Course.objects.create(**course_data)
            self.assertEqual(course.level, level)
    
    def test_course_price_validation(self):
        """Test course price validation"""
        # Test valid price
        course = Course(**self.course_data)
        course.full_clean()  # Should not raise
        
        # Test negative price
        self.course_data['price'] = -1000
        course = Course(**self.course_data)
        with self.assertRaises(ValidationError):
            course.full_clean()
    
    def test_course_capacity_validation(self):
        """Test course capacity validation"""
        # Test valid capacity
        course = Course(**self.course_data)
        course.full_clean()  # Should not raise
        
        # Test zero capacity
        self.course_data['capacity'] = 0
        course = Course(**self.course_data)
        with self.assertRaises(ValidationError):
            course.full_clean()
        
        # Test negative capacity
        self.course_data['capacity'] = -5
        course = Course(**self.course_data)
        with self.assertRaises(ValidationError):
            course.full_clean()
    
    def test_course_duration_validation(self):
        """Test course duration validation"""
        # Test valid duration
        course = Course(**self.course_data)
        course.full_clean()  # Should not raise
        
        # Test zero duration
        self.course_data['duration_weeks'] = 0
        course = Course(**self.course_data)
        with self.assertRaises(ValidationError):
            course.full_clean()
    
    def test_course_slug_generation(self):
        """Test automatic slug generation from title"""
        course = Course.objects.create(**self.course_data)
        expected_slug = slugify(self.course_data['title'])
        self.assertEqual(course.slug, expected_slug)
    
    def test_course_availability_check(self):
        """Test course availability methods"""
        course = Course.objects.create(**self.course_data)
        
        # Course should be available when active and has capacity
        self.assertTrue(course.is_available())
        
        # Course should not be available when inactive
        course.is_active = False
        course.save()
        self.assertFalse(course.is_available())
        
        # Reset and test capacity
        course.is_active = True
        course.save()
        
        # Simulate full enrollment
        course.enrolled_count = course.capacity
        self.assertFalse(course.is_available())
    
    def test_course_get_absolute_url(self):
        """Test course get_absolute_url method"""
        course = Course.objects.create(**self.course_data)
        expected_url = f'/courses/{course.slug}/'
        self.assertEqual(course.get_absolute_url(), expected_url)
    
    def test_course_teacher_relationship(self):
        """Test course-teacher relationship"""
        course = Course.objects.create(**self.course_data)
        self.assertEqual(course.teacher, self.teacher)
        
        # Test reverse relationship
        teacher_courses = self.teacher.courses.all()
        self.assertIn(course, teacher_courses)
    
    def test_course_category_relationship(self):
        """Test course-category relationship"""
        course = Course.objects.create(**self.course_data)
        self.assertEqual(course.category, self.category)
        
        # Test reverse relationship
        category_courses = self.category.courses.all()
        self.assertIn(course, category_courses)


@pytest.mark.django_db
class TestCourseModelPytest:
    """Pytest-style tests for Course model"""
    
    def test_create_course_with_fixtures(self, course):
        """Test creating course with fixtures"""
        assert course.title == 'English Conversation'
        assert course.level == 'beginner'
        assert course.is_active
    
    def test_course_teacher_relationship(self, course, teacher_profile):
        """Test course-teacher relationship"""
        assert course.teacher == teacher_profile
        assert course in teacher_profile.courses.all()
    
    def test_course_category_relationship(self, course, course_category):
        """Test course-category relationship"""
        assert course.category == course_category
        assert course in course_category.courses.all()
    
    def test_multiple_courses_same_category(self, teacher_profile, course_category):
        """Test multiple courses in same category"""
        course1 = Course.objects.create(
            title='Course 1',
            teacher=teacher_profile,
            category=course_category,
            level='beginner',
            price=1000000,
            duration_weeks=4,
            capacity=10
        )
        course2 = Course.objects.create(
            title='Course 2',
            teacher=teacher_profile,
            category=course_category,
            level='intermediate',
            price=1500000,
            duration_weeks=6,
            capacity=15
        )
        
        category_courses = course_category.courses.all()
        assert course1 in category_courses
        assert course2 in category_courses
        assert category_courses.count() >= 2 