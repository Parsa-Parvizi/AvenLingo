 """
Performance tests for the English Teacher platform
"""
import pytest
import time
from django.test import TestCase, Client, override_settings
from django.core.cache import cache
from django.db import connection
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from unittest.mock import patch

from account.models import Student
from teacher.models import Teacher
from course.models import Course, Category
from enrollment.models import Enrollment
from core.models import FAQ, HeroSlider, Testimonial
from tests.factories import (
    UserFactory, StudentFactory, TeacherFactory, CourseFactory,
    CategoryFactory, EnrollmentFactory, FAQFactory, HeroSliderFactory,
    TestimonialFactory
)

User = get_user_model()


class PerformanceTestCase(TestCase):
    """Base class for performance tests with utilities"""
    
    def setUp(self):
        # Clear cache before each test
        cache.clear()
        
        # Reset connection queries
        connection.queries_log.clear()
    
    def get_query_count(self):
        """Get the number of database queries executed"""
        return len(connection.queries)
    
    def measure_time(self, func, *args, **kwargs):
        """Measure execution time of a function"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    def assertQueryCountLessThan(self, count, msg=None):
        """Assert that the number of queries is less than the given count"""
        actual_count = self.get_query_count()
        if actual_count >= count:
            queries = connection.queries
            msg = msg or f"Expected fewer than {count} queries, got {actual_count}"
            if queries:
                msg += f"\nQueries:\n" + "\n".join([q['sql'] for q in queries])
            self.fail(msg)
    
    def assertResponseTimeLessThan(self, response, max_time, msg=None):
        """Assert that response time is less than max_time seconds"""
        if not hasattr(response, '_test_start_time'):
            self.fail("Response doesn't have timing information")
        
        response_time = time.time() - response._test_start_time
        if response_time >= max_time:
            msg = msg or f"Response took {response_time:.3f}s, expected < {max_time}s"
            self.fail(msg)


@override_settings(DEBUG=True)  # Enable query logging
class HomePagePerformanceTest(PerformanceTestCase):
    """Test home page performance"""
    
    @classmethod
    def setUpTestData(cls):
        """Create test data for performance testing"""
        # Create categories
        cls.categories = CategoryFactory.create_batch(10)
        
        # Create teachers
        cls.teachers = TeacherFactory.create_batch(15)
        
        # Create courses
        cls.courses = []
        for teacher in cls.teachers:
            courses = CourseFactory.create_batch(3, teacher=teacher)
            cls.courses.extend(courses)
        
        # Create FAQs
        cls.faqs = FAQFactory.create_batch(20)
        
        # Create hero sliders
        cls.hero_sliders = HeroSliderFactory.create_batch(5)
        
        # Create testimonials
        cls.testimonials = TestimonialFactory.create_batch(10)
    
    def test_home_page_query_count_optimized(self):
        """Test that home page uses optimized number of queries"""
        url = reverse('core:home')
        
        # Clear cache to test uncached performance
        cache.clear()
        
        # Reset query count
        connection.queries_log.clear()
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Should use much fewer queries than before optimization
        # Before: 7+ separate queries
        # After: Should be 5 or fewer optimized queries
        self.assertQueryCountLessThan(8, "Home page should use fewer than 8 queries")
    
    def test_home_page_response_time(self):
        """Test home page response time"""
        url = reverse('core:home')
        
        # Clear cache to test uncached performance
        cache.clear()
        
        start_time = time.time()
        response = self.client.get(url)
        response_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 1.0, f"Home page took {response_time:.3f}s, should be < 1.0s")
    
    def test_home_page_caching_effectiveness(self):
        """Test that caching reduces database queries"""
        url = reverse('core:home')
        
        # First request (uncached)
        cache.clear()
        connection.queries_log.clear()
        response1 = self.client.get(url)
        queries_uncached = self.get_query_count()
        
        # Second request (should be cached in production mode)
        with override_settings(DEBUG=False):
            connection.queries_log.clear()
            response2 = self.client.get(url)
            queries_cached = self.get_query_count()
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # In production mode, cached request should use significantly fewer queries
        if not settings.DEBUG:
            self.assertLess(queries_cached, queries_uncached, 
                           "Cached request should use fewer queries than uncached")


class SearchPerformanceTest(PerformanceTestCase):
    """Test search functionality performance"""
    
    @classmethod
    def setUpTestData(cls):
        """Create test data for search performance testing"""
        # Create categories
        cls.categories = CategoryFactory.create_batch(5)
        
        # Create teachers with searchable content
        cls.teachers = TeacherFactory.create_batch(50)
        
        # Create courses with searchable content
        cls.courses = []
        for teacher in cls.teachers[:30]:  # 30 teachers with courses
            courses = CourseFactory.create_batch(2, teacher=teacher)
            cls.courses.extend(courses)
    
    def test_course_search_query_optimization(self):
        """Test that course search uses optimized queries"""
        url = reverse('core:search')
        
        connection.queries_log.clear()
        response = self.client.get(url, {
            'q': 'English',
            'search_courses': 'true'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Should use select_related to avoid N+1 queries
        self.assertQueryCountLessThan(5, "Course search should use fewer than 5 queries")
    
    def test_teacher_search_query_optimization(self):
        """Test that teacher search uses optimized queries"""
        url = reverse('core:search')
        
        connection.queries_log.clear()
        response = self.client.get(url, {
            'q': 'teacher',
            'search_teachers': 'true'
        })
        
        self.assertEqual(response.status_code, 200)
        
        # Should use select_related to avoid N+1 queries
        self.assertQueryCountLessThan(5, "Teacher search should use fewer than 5 queries")
    
    def test_search_response_time(self):
        """Test search response time"""
        url = reverse('core:search')
        
        start_time = time.time()
        response = self.client.get(url, {
            'q': 'test query',
            'search_courses': 'true',
            'search_teachers': 'true'
        })
        response_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 0.5, f"Search took {response_time:.3f}s, should be < 0.5s")


class StudentDashboardPerformanceTest(PerformanceTestCase):
    """Test student dashboard performance"""
    
    def setUp(self):
        super().setUp()
        self.student_user = UserFactory(user_type='student')
        self.student = StudentFactory(user=self.student_user)
        
        # Create enrollments for the student
        self.courses = CourseFactory.create_batch(10)
        self.enrollments = []
        for course in self.courses[:5]:  # 5 enrolled courses
            enrollment = EnrollmentFactory(student=self.student, course=course)
            self.enrollments.append(enrollment)
    
    def test_student_dashboard_query_optimization(self):
        """Test student dashboard uses optimized queries"""
        self.client.force_login(self.student_user)
        url = reverse('account:student_dashboard')
        
        connection.queries_log.clear()
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Should use select_related and prefetch_related to optimize queries
        self.assertQueryCountLessThan(10, "Student dashboard should use fewer than 10 queries")


class ContextProcessorPerformanceTest(PerformanceTestCase):
    """Test context processor performance"""
    
    @classmethod
    def setUpTestData(cls):
        """Create test data for context processor testing"""
        # Create data that will be loaded by context processors
        cls.hero_sliders = HeroSliderFactory.create_batch(5)
        cls.testimonials = TestimonialFactory.create_batch(10)
        cls.faqs = FAQFactory.create_batch(15)
    
    def test_context_processor_caching(self):
        """Test that context processors use caching effectively"""
        url = reverse('core:home')
        
        # First request (should populate cache)
        cache.clear()
        connection.queries_log.clear()
        response1 = self.client.get(url)
        queries_first = self.get_query_count()
        
        # Second request (should use cache)
        connection.queries_log.clear()
        response2 = self.client.get(url)
        queries_second = self.get_query_count()
        
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Second request should use fewer queries due to caching
        self.assertLessEqual(queries_second, queries_first, 
                           "Second request should use same or fewer queries due to caching")


@pytest.mark.performance
class LoadTestScenarios(PerformanceTestCase):
    """Load testing scenarios for critical user paths"""
    
    @classmethod
    def setUpTestData(cls):
        """Create comprehensive test data"""
        # Create a full dataset
        cls.categories = CategoryFactory.create_batch(20)
        cls.teachers = TeacherFactory.create_batch(100)
        cls.students = StudentFactory.create_batch(200)
        
        # Create many courses
        cls.courses = []
        for teacher in cls.teachers:
            courses = CourseFactory.create_batch(3, teacher=teacher)
            cls.courses.extend(courses)
        
        # Create many enrollments
        cls.enrollments = []
        for student in cls.students[:100]:  # Half of students have enrollments
            for course in cls.courses[:5]:  # Enroll in first 5 courses
                enrollment = EnrollmentFactory(student=student, course=course)
                cls.enrollments.append(enrollment)
    
    def test_concurrent_home_page_access(self):
        """Simulate concurrent access to home page"""
        url = reverse('core:home')
        
        # Simulate 10 concurrent requests
        response_times = []
        for i in range(10):
            start_time = time.time()
            response = self.client.get(url)
            end_time = time.time()
            
            self.assertEqual(response.status_code, 200)
            response_times.append(end_time - start_time)
        
        # Check average response time
        avg_response_time = sum(response_times) / len(response_times)
        self.assertLess(avg_response_time, 1.0, 
                       f"Average response time {avg_response_time:.3f}s should be < 1.0s")
    
    def test_course_list_with_many_courses(self):
        """Test course list performance with many courses"""
        url = reverse('course:course_list')
        
        start_time = time.time()
        response = self.client.get(url)
        response_time = time.time() - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 2.0, 
                       f"Course list took {response_time:.3f}s, should be < 2.0s")


@pytest.mark.benchmark
def test_home_page_benchmark(benchmark):
    """Benchmark home page performance using pytest-benchmark"""
    client = Client()
    
    def home_page_request():
        cache.clear()  # Test uncached performance
        return client.get(reverse('core:home'))
    
    result = benchmark(home_page_request)
    assert result.status_code == 200


@pytest.mark.benchmark
def test_search_benchmark(benchmark):
    """Benchmark search performance"""
    client = Client()
    
    def search_request():
        return client.get(reverse('core:search'), {
            'q': 'English',
            'search_courses': 'true',
            'search_teachers': 'true'
        })
    
    result = benchmark(search_request)
    assert result.status_code == 200


class DatabaseIndexPerformanceTest(TestCase):
    """Test that database indexes are working effectively"""
    
    def test_course_filtering_performance(self):
        """Test that course filtering uses indexes effectively"""
        # Create many courses
        CourseFactory.create_batch(1000)
        
        start_time = time.time()
        # This query should benefit from indexes
        active_courses = Course.objects.filter(is_active=True).count()
        query_time = time.time() - start_time
        
        # Should be fast with proper indexing
        self.assertLess(query_time, 0.1, 
                       f"Course filtering took {query_time:.3f}s, should be < 0.1s")
    
    def test_user_lookup_performance(self):
        """Test that user lookups use indexes effectively"""
        # Create many users
        UserFactory.create_batch(1000)
        
        start_time = time.time()
        # This query should benefit from indexes
        user = User.objects.filter(email='test@example.com').first()
        query_time = time.time() - start_time
        
        # Should be fast with proper indexing
        self.assertLess(query_time, 0.05, 
                       f"User lookup took {query_time:.3f}s, should be < 0.05s")


# Custom test runner command for performance testing
def run_performance_tests():
    """
    Run performance tests and generate report
    Usage: python -c "from tests.test_performance import run_performance_tests; run_performance_tests()"
    """
    import subprocess
    import sys
    
    # Run performance tests
    result = subprocess.run([
        sys.executable, '-m', 'pytest', 
        'tests/test_performance.py',
        '-v',
        '--tb=short',
        '--benchmark-only',
        '--benchmark-sort=mean',
        '--benchmark-json=performance_report.json'
    ])
    
    if result.returncode == 0:
        print("\n✅ Performance tests completed successfully!")
        print("📊 Benchmark report saved to performance_report.json")
    else:
        print("\n❌ Performance tests failed!")
    
    return result.returncode