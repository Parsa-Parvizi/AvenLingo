#!/usr/bin/env python
"""
Comprehensive test runner script for the English Teacher platform
Provides various options for running different types of tests
"""
import os
import sys
import django
import argparse
from django.conf import settings
from django.test.utils import get_runner
import subprocess


def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EnglishTeacher.test_settings')
    django.setup()


def run_django_tests(test_labels=None, verbosity=2, interactive=False, failfast=False, keepdb=False):
    """Run Django tests using Django's test runner"""
    setup_django()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(
        verbosity=verbosity,
        interactive=interactive,
        failfast=failfast,
        keepdb=keepdb
    )
    
    if not test_labels:
        test_labels = [
            'account.tests',
            'core.tests', 
            'course.tests',
            'enrollment.tests',
            'teacher.tests',
            'contact.tests',
            'tests'
        ]
    
    failures = test_runner.run_tests(test_labels)
    return failures


def run_pytest(args=None):
    """Run tests using pytest"""
    cmd = ['pytest']
    
    if args:
        cmd.extend(args)
    else:
        # Default pytest arguments
        cmd.extend([
            '--tb=short',
            '--strict-markers',
            '--disable-warnings',
            '--reuse-db',
            '--nomigrations',
            '-v'
        ])
    
    return subprocess.call(cmd)


def run_coverage_tests():
    """Run tests with coverage reporting"""
    cmd = [
        'pytest',
        '--cov=.',
        '--cov-report=html',
        '--cov-report=term-missing',
        '--cov-report=xml',
        '--cov-fail-under=80',
        '--tb=short',
        '--disable-warnings',
        '--reuse-db',
        '--nomigrations'
    ]
    
    return subprocess.call(cmd)


def run_unit_tests():
    """Run only unit tests"""
    cmd = [
        'pytest',
        '-m', 'unit',
        '--tb=short',
        '--disable-warnings',
        '--reuse-db',
        '--nomigrations',
        '-v'
    ]
    
    return subprocess.call(cmd)


def run_integration_tests():
    """Run only integration tests"""
    cmd = [
        'pytest',
        '-m', 'integration',
        '--tb=short',
        '--disable-warnings',
        '--reuse-db',
        '--nomigrations',
        '-v'
    ]
    
    return subprocess.call(cmd)


def run_model_tests():
    """Run only model tests"""
    cmd = [
        'pytest',
        '**/test_models.py',
        '--tb=short',
        '--disable-warnings',
        '--reuse-db',
        '--nomigrations',
        '-v'
    ]
    
    return subprocess.call(cmd)


def run_view_tests():
    """Run only view tests"""
    cmd = [
        'pytest',
        '**/test_views.py',
        '--tb=short',
        '--disable-warnings',
        '--reuse-db',
        '--nomigrations',
        '-v'
    ]
    
    return subprocess.call(cmd)


def run_form_tests():
    """Run only form tests"""
    cmd = [
        'pytest',
        '**/test_forms.py',
        '--tb=short',
        '--disable-warnings',
        '--reuse-db',
        '--nomigrations',
        '-v'
    ]
    
    return subprocess.call(cmd)


def run_specific_app_tests(app_name):
    """Run tests for a specific app"""
    cmd = [
        'pytest',
        f'{app_name}/',
        '--tb=short',
        '--disable-warnings',
        '--reuse-db',
        '--nomigrations',
        '-v'
    ]
    
    return subprocess.call(cmd)


def run_fast_tests():
    """Run fast tests only (exclude slow tests)"""
    cmd = [
        'pytest',
        '-m', 'not slow',
        '--tb=short',
        '--disable-warnings',
        '--reuse-db',
        '--nomigrations',
        '-v'
    ]
    
    return subprocess.call(cmd)


def run_slow_tests():
    """Run slow tests only"""
    cmd = [
        'pytest',
        '-m', 'slow',
        '--tb=short',
        '--disable-warnings',
        '--reuse-db',
        '--nomigrations',
        '-v'
    ]
    
    return subprocess.call(cmd)


def create_test_database():
    """Create and migrate test database"""
    setup_django()
    
    from django.core.management import execute_from_command_line
    
    # Create test database
    execute_from_command_line(['manage.py', 'migrate', '--settings=EnglishTeacher.test_settings'])
    
    print("Test database created and migrated successfully!")


def load_test_fixtures():
    """Load test fixtures"""
    setup_django()
    
    from django.core.management import execute_from_command_line
    
    # Load fixtures
    fixtures = [
        'tests/fixtures/sample_data.json'
    ]
    
    for fixture in fixtures:
        if os.path.exists(fixture):
            execute_from_command_line([
                'manage.py', 
                'loaddata', 
                fixture,
                '--settings=EnglishTeacher.test_settings'
            ])
            print(f"Loaded fixture: {fixture}")
        else:
            print(f"Fixture not found: {fixture}")


def generate_test_data():
    """Generate test data using factories"""
    setup_django()
    
    from tests.factories import create_complete_test_dataset
    
    print("Generating test data...")
    dataset = create_complete_test_dataset()
    
    print(f"Created:")
    print(f"  - {len(dataset['teachers'])} teachers")
    print(f"  - {len(dataset['students'])} students") 
    print(f"  - {len(dataset['courses'])} courses")
    print(f"  - {len(dataset['enrollments'])} enrollments")
    print(f"  - {len(dataset['payments'])} payments")
    print("Test data generated successfully!")


def main():
    """Main function to handle command line arguments"""
    parser = argparse.ArgumentParser(
        description='Test runner for English Teacher platform',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests with pytest
  python run_tests.py --django          # Run tests with Django test runner
  python run_tests.py --coverage        # Run tests with coverage
  python run_tests.py --unit            # Run only unit tests
  python run_tests.py --integration     # Run only integration tests
  python run_tests.py --models          # Run only model tests
  python run_tests.py --views           # Run only view tests
  python run_tests.py --forms           # Run only form tests
  python run_tests.py --app account     # Run tests for account app
  python run_tests.py --fast            # Run fast tests only
  python run_tests.py --slow            # Run slow tests only
  python run_tests.py --setup-db        # Create and migrate test database
  python run_tests.py --load-fixtures   # Load test fixtures
  python run_tests.py --generate-data   # Generate test data with factories
        """
    )
    
    # Test running options
    parser.add_argument('--django', action='store_true', help='Use Django test runner')
    parser.add_argument('--coverage', action='store_true', help='Run tests with coverage')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--models', action='store_true', help='Run model tests only')
    parser.add_argument('--views', action='store_true', help='Run view tests only')
    parser.add_argument('--forms', action='store_true', help='Run form tests only')
    parser.add_argument('--fast', action='store_true', help='Run fast tests only')
    parser.add_argument('--slow', action='store_true', help='Run slow tests only')
    parser.add_argument('--app', help='Run tests for specific app')
    
    # Test setup options
    parser.add_argument('--setup-db', action='store_true', help='Create and migrate test database')
    parser.add_argument('--load-fixtures', action='store_true', help='Load test fixtures')
    parser.add_argument('--generate-data', action='store_true', help='Generate test data')
    
    # Test configuration options
    parser.add_argument('--failfast', action='store_true', help='Stop on first failure')
    parser.add_argument('--keepdb', action='store_true', help='Preserve test database')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    # Custom pytest arguments
    parser.add_argument('--pytest-args', nargs='*', help='Additional pytest arguments')
    
    args = parser.parse_args()
    
    # Handle setup commands
    if args.setup_db:
        create_test_database()
        return
    
    if args.load_fixtures:
        load_test_fixtures()
        return
    
    if args.generate_data:
        generate_test_data()
        return
    
    # Run tests based on arguments
    if args.django:
        failures = run_django_tests(
            verbosity=2 if args.verbose else 1,
            failfast=args.failfast,
            keepdb=args.keepdb
        )
        sys.exit(failures)
    elif args.coverage:
        return run_coverage_tests()
    elif args.unit:
        return run_unit_tests()
    elif args.integration:
        return run_integration_tests()
    elif args.models:
        return run_model_tests()
    elif args.views:
        return run_view_tests()
    elif args.forms:
        return run_form_tests()
    elif args.fast:
        return run_fast_tests()
    elif args.slow:
        return run_slow_tests()
    elif args.app:
        return run_specific_app_tests(args.app)
    else:
        # Default: run all tests with pytest
        pytest_args = args.pytest_args or []
        return run_pytest(pytest_args)


if __name__ == '__main__':
    main() 