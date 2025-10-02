from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

import random
import string
from datetime import timedelta, date

from account.models import Student, TeacherApplication
from account.models import Teacher
from course.models import Category, Course, LANGUAGE_CHOICES
from enrollment.models import Enrollment
from core.models import AdviceRequest, DeterminationRequest, CollabrateRequest, RequestCourse


def random_string(length: int = 8) -> str:
  letters = string.ascii_lowercase
  return ''.join(random.choice(letters) for _ in range(length))


def random_phone() -> str:
  return '09' + ''.join(random.choice('0123456789') for _ in range(9))


def ensure_superuser(User, email: str = 'admin@example.com', password: str = 'Admin!12345'):
  if not User.objects.filter(email=email).exists():
    print(f"Creating superuser {email}")
    User.objects.create_superuser(
      email=email,
      password=password,
      first_name='Site',
      last_name='Admin',
      user_type='admin',
    )
  else:
    print(f"Superuser {email} already exists")


class Command(BaseCommand):
  help = "Seed high-quality demo data: users (students/teachers/superuser), categories, courses, enrollments, requests, applications"

  def add_arguments(self, parser):
    parser.add_argument('--students', type=int, default=15, help='Number of student users to create')
    parser.add_argument('--teachers', type=int, default=5, help='Number of teachers to create')
    parser.add_argument('--courses', type=int, default=20, help='Number of courses to create')
    parser.add_argument('--enrollments', type=int, default=50, help='Number of enrollments to create')
    parser.add_argument('--requests', type=int, default=25, help='Number of each request type to create')
    parser.add_argument('--applications', type=int, default=10, help='Number of teacher applications to create')
    parser.add_argument('--superuser_email', type=str, default='admin@example.com', help='Superuser email')
    parser.add_argument('--superuser_password', type=str, default='Admin!12345', help='Superuser password')
    parser.add_argument('--fresh', action='store_true', help='Delete existing demo data before seeding')

  @transaction.atomic
  def handle(self, *args, **options):
    User = get_user_model()

    num_students = options['students']
    num_teachers = options['teachers']
    num_courses = options['courses']
    num_enrollments = options['enrollments']
    num_requests = options['requests']
    num_applications = options['applications']

    if options['fresh']:
      self.stdout.write(self.style.WARNING('Cleaning existing demo data...'))
      Enrollment.objects.all().delete()
      Course.objects.all().delete()
      Category.objects.all().delete()
      Teacher.objects.all().delete()
      Student.objects.all().delete()
      TeacherApplication.objects.all().delete()
      AdviceRequest.objects.all().delete()
      DeterminationRequest.objects.all().delete()
      CollabrateRequest.objects.all().delete()
      RequestCourse.objects.all().delete()
      User.objects.exclude(is_superuser=True).delete()

    self.stdout.write(self.style.SUCCESS('Ensuring superuser...'))
    ensure_superuser(User, options['superuser_email'], options['superuser_password'])

    # Create students
    self.stdout.write(self.style.SUCCESS('Creating students...'))
    students = []
    for i in range(num_students):
      email = f"student{i+1}@example.com"
      user, created = User.objects.get_or_create(
        email=email,
        defaults={
          'first_name': f'Student{i+1}',
          'last_name': 'User',
          'user_type': 'student',
          'is_active': True,
        }
      )
      if created:
        user.set_password('student1234')
        user.save()
      student_profile, _ = Student.objects.get_or_create(
        user=user,
        defaults={
          'phone_number': random_phone(),
          'english_level': random.choice(['A1', 'A2', 'B1', 'B2', 'C1']),
          'goals': random.choice(['Speaking', 'IELTS', 'Business English', 'General English']),
        }
      )
      students.append(student_profile)

    # Create teacher users and legacy teacher profiles used by Course model
    self.stdout.write(self.style.SUCCESS('Creating teachers...'))
    teachers = []
    for i in range(num_teachers):
      email = f"teacher{i+1}@example.com"
      user, created = User.objects.get_or_create(
        email=email,
        defaults={
          'first_name': f'Teacher{i+1}',
          'last_name': 'User',
          'user_type': 'teacher',
          'is_active': True,
          'is_staff': False,  # معلمان نباید staff باشند
        }
      )
      if created:
        user.set_password('teacher1234')
        user.save()
      legacy_teacher, _ = Teacher.objects.get_or_create(
        user=user,
        defaults={
          'full_name': f'Teacher {i+1} User',
          'bio': 'Experienced language instructor with a passion for teaching.',
          'expertise': random.choice(['IELTS', 'Conversation', 'Grammar', 'Writing', 'Kids English']),
          'phone_number': random_phone(),
          'is_active': True,
          'registration_status': random.choice(['approved', 'registered'])
        }
      )
      teachers.append(legacy_teacher)

    # Create categories
    self.stdout.write(self.style.SUCCESS('Creating categories...'))
    base_categories = [
      ('مکالمه', 'conversation'),
      ('گرامر', 'grammar'),
      ('IELTS', 'ielts'),
      ('کودکان', 'kids'),
      ('واژگان', 'vocabulary'),
    ]
    categories = []
    for name, key in base_categories:
      lang = random.choice([lc[0] for lc in LANGUAGE_CHOICES])
      category, _ = Category.objects.get_or_create(
        name=name,
        defaults={
          'description': f'دسته‌بندی {name} برای زبان‌آموزان',
          'language': lang,
          'is_active': True,
        }
      )
      categories.append(category)

    # Create courses
    self.stdout.write(self.style.SUCCESS('Creating courses...'))
    courses = []
    level_choices = ['beginner', 'intermediate', 'advanced']
    age_choices = ['kids', 'teens', 'adults']
    class_types = ['general', 'grammar', 'writing', 'speaking', 'listening', 'reading', 'vocabulary', 'conversation', 'exam', 'ielts']

    for i in range(num_courses):
      teacher = random.choice(teachers) if teachers else None
      category = random.choice(categories) if categories else None
      title = f"دوره {random.choice(['IELTS','مکالمه','گرامر','کودکان','واژگان'])} سطح {random.choice(['1','2','3','4'])} - {random_string(4)}"
      price = random.choice([0, 250000, 350000, 500000, 750000, 1000000])
      is_free = price == 0
      start_delta = random.randint(-30, 30)
      start_date = date.today() + timedelta(days=start_delta)
      duration = random.choice(['شنبه-سه‌شنبه 18:00', 'دوشنبه-پنج‌شنبه 10:00', 'یکشنبه‌ها 16:00'])

      course = Course.objects.create(
        status=random.choice(['pending','approved','published','published','published']),
        title=title,
        description='این دوره برای بهبود مهارت‌های زبان انگلیسی طراحی شده است.',
        short_description='مرور سریع سرفصل‌ها و اهداف دوره.',
        teacher=teacher,
        category=category,
        start_date=start_date,
        end_date=start_date + timedelta(days=30),
        duration=duration,
        total_hours=random.choice([8, 10, 12, 16, 20]),
        level=random.choice(level_choices),
        age_group=random.choice(age_choices),
        class_type=random.choice(class_types),
        capacity=random.choice([10, 15, 20, 25]),
        price=price,
        location=random.choice(['آنلاین', 'شعبه ونک', 'شعبه تجریش']),
        is_active=True,
        is_free=is_free,
        is_featured=random.choice([True, False, False]),
        is_online=random.choice([True, False]),
      )
      courses.append(course)

    # Create enrollments (only for published/approved courses)
    self.stdout.write(self.style.SUCCESS('Creating enrollments...'))
    published_courses = [c for c in courses if c.status in ['approved','published']]
    if not published_courses:
      published_courses = courses

    created_pairs = set()
    for _ in range(num_enrollments):
      student = random.choice(students)
      course = random.choice(published_courses)
      pair_key = (student.id, course.id)
      if pair_key in created_pairs:
        continue
      created_pairs.add(pair_key)

      status = random.choices(['pending','confirmed','completed','cancelled'], weights=[2,6,1,1])[0]
      payment_status = 'paid' if status in ['confirmed','completed'] and course.price > 0 else random.choice(['unpaid','partial'])
      amount_paid = 0
      if payment_status == 'paid':
        amount_paid = int(course.price)
      elif payment_status == 'partial' and course.price:
        amount_paid = int(course.price) // random.choice([2,3])

      Enrollment.objects.create(
        student=student,
        course=course,
        status=status,
        payment_status=payment_status,
        enrolled_at=timezone.now() - timedelta(days=random.randint(0, 20)),
        note=random.choice(['', 'درخواست تغییر زمان کلاس', 'تماس تلفنی برای هماهنگی']),
        amount_paid=amount_paid,
        discount_applied=random.choice([0, 0, 50000, 100000]),
        enrollment_source=random.choice(['website','phone','in_person','referral','social_media']),
        completion_percentage=0 if status in ['pending','confirmed'] else random.choice([50, 80, 100]),
      )

    # Create contact-related requests
    self.stdout.write(self.style.SUCCESS('Creating advice/determination/collaboration/course requests...'))
    for i in range(num_requests):
      AdviceRequest.objects.create(
        name=f"مشاوره‌جو {i+1}",
        email=f"advice{i+1}@example.com",
        phone=random_phone(),
        message=f"نیاز به مشاوره در مورد انتخاب دوره دارم. کد {random_string(6)}",
        submitted_at=timezone.now() - timedelta(days=random.randint(0, 15)),
      )
      DeterminationRequest.objects.create(
        name=f"تعیین‌سطح {i+1}",
        email=f"placement{i+1}@example.com",
        phone=random_phone(),
        message=f"درخواست تعیین سطح آنلاین. کد {random_string(6)}",
        submitted_at=timezone.now() - timedelta(days=random.randint(0, 15)),
      )
      CollabrateRequest.objects.create(
        name=f"متقاضی همکاری {i+1}",
        email=f"collab{i+1}@example.com",
        phone=random_phone(),
        message=f"تمایل به همکاری به عنوان مدرس. رزومه ارسال شد. {random_string(5)}",
        submitted_at=timezone.now() - timedelta(days=random.randint(0, 15)),
        status=random.choice(['pending','approved','rejected']),
      )
      RequestCourse.objects.create(
        name=f"درخواست‌دهنده {i+1}",
        email=f"request{i+1}@example.com",
        phone=random_phone(),
        course_title=f"درخواست دوره {random.choice(['IELTS','مکالمه','گرامر','کودکان'])} سطح {random.choice(['A1','A2','B1','B2'])}",
        description=f"توضیحات تکمیلی برای درخواست دوره. {random_string(10)}",
        created_at=timezone.now() - timedelta(days=random.randint(0, 15)),
      )

    # Create teacher applications
    self.stdout.write(self.style.SUCCESS('Creating teacher applications...'))
    for i in range(num_applications):
      TeacherApplication.objects.create(
        first_name=f"مدرس{i+1}",
        last_name="مثال",
        email=f"tapp{i+1}@example.com",
        phone_number=random_phone(),
        education="کارشناسی مترجمی زبان انگلیسی",
        experience=f"{random.choice([2,3,5,8])} سال تجربه تدریس",
        certifications="CELTA, TESOL",
        specialties=random.choice(['IELTS','Speaking','Grammar','Kids English']),
        motivation="علاقه‌مند به همکاری با آکادمی شما هستم.",
        status=random.choice(['pending','accepted','rejected']),
        submitted_at=timezone.now() - timedelta(days=random.randint(0, 20)),
      )

    self.stdout.write(self.style.SUCCESS('Demo data seeding completed successfully.')) 