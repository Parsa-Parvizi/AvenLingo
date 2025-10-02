from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import connection

from account.models import Student, TeacherApplication, Teacher
from course.models import Category, Course
from enrollment.models import Enrollment
from core.models import AdviceRequest, DeterminationRequest, CollabrateRequest, RequestCourse


class Command(BaseCommand):
    help = "Clean old data while preserving superuser"

    def add_arguments(self, parser):
        parser.add_argument('--confirm', action='store_true', help='Confirm deletion of old data')

    def handle(self, *args, **options):
        User = get_user_model()

        if not options['confirm']:
            self.stdout.write(self.style.WARNING('This will delete all data except superusers. Use --confirm to proceed.'))
            return

        self.stdout.write(self.style.WARNING('Cleaning old data (preserving superuser)...'))
        
        # Count existing data
        old_students = Student.objects.count()
        old_teachers = Teacher.objects.count()
        old_courses = Course.objects.count()
        old_enrollments = Enrollment.objects.count()
        old_applications = TeacherApplication.objects.count()
        old_advice = AdviceRequest.objects.count()
        old_determination = DeterminationRequest.objects.count()
        old_collab = CollabrateRequest.objects.count()
        old_requests = RequestCourse.objects.count()
        
        self.stdout.write(f'Found: {old_students} students, {old_teachers} teachers, {old_courses} courses, {old_enrollments} enrollments')
        self.stdout.write(f'Found: {old_applications} applications, {old_advice} advice requests, {old_determination} determination requests')
        self.stdout.write(f'Found: {old_collab} collaboration requests, {old_requests} course requests')
        
        # Use raw SQL to handle deletion without transaction issues
        with connection.cursor() as cursor:
            # Delete many-to-many relationships first if table exists
            try:
                cursor.execute("DELETE FROM course_course_students")
                self.stdout.write('Cleared course_course_students relationships')
            except Exception as e:
                self.stdout.write(f'Note: course_course_students table does not exist: {e}')
            
            # Delete enrollments
            cursor.execute("DELETE FROM enrollment_enrollment")
            self.stdout.write('Deleted enrollments')
            
            # Delete courses
            cursor.execute("DELETE FROM course_course")
            self.stdout.write('Deleted courses')
            
            # Delete categories
            cursor.execute("DELETE FROM course_category")
            self.stdout.write('Deleted categories')
            
            # Delete teachers
            cursor.execute("DELETE FROM account_teacher")
            self.stdout.write('Deleted teachers')
            
            # Delete students
            cursor.execute("DELETE FROM account_student")
            self.stdout.write('Deleted students')
            
            # Delete teacher applications
            cursor.execute("DELETE FROM account_teacherapplication")
            self.stdout.write('Deleted teacher applications')
            
            # Delete requests
            cursor.execute("DELETE FROM core_advicerequest")
            cursor.execute("DELETE FROM core_determinationrequest")
            cursor.execute("DELETE FROM core_collabraterequest")
            cursor.execute("DELETE FROM core_requestcourse")
            self.stdout.write('Deleted all request types')
            
            # Delete non-superuser accounts
            cursor.execute("DELETE FROM account_user WHERE is_superuser = FALSE")
            self.stdout.write('Deleted non-superuser accounts')
        
        self.stdout.write(self.style.SUCCESS(f'Cleaned up: {old_students} students, {old_teachers} teachers, {old_courses} courses, {old_enrollments} enrollments'))
        self.stdout.write(self.style.SUCCESS(f'Cleaned up: {old_applications} applications, {old_advice} advice requests, {old_determination} determination requests'))
        self.stdout.write(self.style.SUCCESS(f'Cleaned up: {old_collab} collaboration requests, {old_requests} course requests'))
        self.stdout.write(self.style.SUCCESS('Old data cleanup completed successfully!'))
