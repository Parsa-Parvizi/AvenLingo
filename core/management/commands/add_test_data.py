from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

import random
import string
from datetime import timedelta, date

from account.models import Student, TeacherApplication, Teacher
from course.models import Category, Course, LANGUAGE_CHOICES
from enrollment.models import Enrollment
from core.models import AdviceRequest, DeterminationRequest, CollabrateRequest, RequestCourse


def random_string(length: int = 8) -> str:
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))


def random_phone() -> str:
    return '09' + ''.join(random.choice('0123456789') for _ in range(9))


class Command(BaseCommand):
    help = "Add fresh test data without deleting existing data"

    def add_arguments(self, parser):
        parser.add_argument('--students', type=int, default=20, help='Number of student users to create')
        parser.add_argument('--teachers', type=int, default=8, help='Number of teachers to create')
        parser.add_argument('--courses', type=int, default=25, help='Number of courses to create')
        parser.add_argument('--enrollments', type=int, default=60, help='Number of enrollments to create')
        parser.add_argument('--requests', type=int, default=30, help='Number of each request type to create')
        parser.add_argument('--applications', type=int, default=15, help='Number of teacher applications to create')

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        num_students = options['students']
        num_teachers = options['teachers']
        num_courses = options['courses']
        num_enrollments = options['enrollments']
        num_requests = options['requests']
        num_applications = options['applications']

        self.stdout.write(self.style.SUCCESS('Adding fresh test data...'))

        # Create students
        self.stdout.write(self.style.SUCCESS('Creating students...'))
        students = []
        persian_names = [
            ('علی', 'احمدی'), ('فاطمه', 'محمدی'), ('حسن', 'رضایی'), ('زهرا', 'کریمی'),
            ('محمد', 'حسینی'), ('مریم', 'نوری'), ('رضا', 'صادقی'), ('نرگس', 'موسوی'),
            ('امیر', 'جعفری'), ('سارا', 'قاسمی'), ('حسین', 'مهدوی'), ('لیلا', 'باقری'),
            ('مهدی', 'کاظمی'), ('فریبا', 'شریفی'), ('سعید', 'طاهری'), ('ناهید', 'رحمانی'),
            ('کامران', 'فرهادی'), ('شهرزاد', 'نوری'), ('بابک', 'میرزایی'), ('گلناز', 'صالحی')
        ]
        
        for i in range(num_students):
            first_name, last_name = persian_names[i % len(persian_names)]
            email = f"test_student{i+1}@example.com"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
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
                        'english_level': random.choice(['A1', 'A2', 'B1', 'B2', 'C1', 'C2']),
                        'goals': random.choice([
                            'بهبود مکالمه', 'آمادگی آیلتس', 'انگلیسی تجاری', 
                            'انگلیسی عمومی', 'آمادگی تافل', 'انگلیسی کودکان'
                        ]),
                        'address': f'تهران، منطقه {random.choice([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22])}',
                    }
                )
                students.append(student_profile)

        # Create teacher applications first
        self.stdout.write(self.style.SUCCESS('Creating teacher applications...'))
        teacher_applications = []
        for i in range(num_applications):
            first_name, last_name = persian_names[i % len(persian_names)]
            app = TeacherApplication.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=f"test_tapp{i+1}@example.com",
                phone_number=random_phone(),
                education=random.choice([
                    "کارشناسی مترجمی زبان انگلیسی",
                    "کارشناسی ارشد آموزش زبان انگلیسی",
                    "دکتری زبان‌شناسی",
                    "کارشناسی زبان و ادبیات انگلیسی"
                ]),
                experience=f"{random.choice([2,3,5,8,10,12])} سال تجربه تدریس",
                certifications=random.choice([
                    "CELTA, TESOL",
                    "TEFL, IELTS Trainer",
                    "Cambridge Assessment",
                    "British Council Certified"
                ]),
                specialties=random.choice([
                    'IELTS, Speaking',
                    'Grammar, Writing',
                    'Kids English, Conversation',
                    'Business English, TOEFL'
                ]),
                motivation="علاقه‌مند به همکاری با آکادمی شما هستم و تجربه تدریس در این زمینه دارم.",
                status=random.choice(['pending', 'accepted', 'rejected']),
                submitted_at=timezone.now() - timedelta(days=random.randint(0, 30)),
            )
            teacher_applications.append(app)

        # Create teachers
        self.stdout.write(self.style.SUCCESS('Creating teachers...'))
        teachers = []
        for i in range(num_teachers):
            first_name, last_name = persian_names[i % len(persian_names)]
            email = f"test_teacher{i+1}@example.com"
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'user_type': 'teacher',
                    'is_active': True,
                    'is_staff': False,  # معلمان نباید staff باشند
                }
            )
            if created:
                user.set_password('teacher1234')
                user.save()
                
                # Get a unique application for this teacher
                application = teacher_applications[i]  # Use index to ensure uniqueness
                
                teacher_profile = Teacher.objects.create(
                    user=user,
                    application=application,
                    bio=f'مدرس با تجربه در زمینه آموزش زبان انگلیسی با {random.choice([3,5,8,10])} سال سابقه تدریس.',
                    specialties=random.choice([
                        'IELTS, Speaking, Grammar',
                        'Kids English, Conversation',
                        'Business English, Writing',
                        'TOEFL, Listening, Reading'
                    ]),
                    hourly_rate=random.choice([50000, 75000, 100000, 125000, 150000]),
                    is_active=True,
                    is_verified=random.choice([True, True, False]),  # 2/3 chance of being verified
                    education_level=random.choice(['کارشناسی', 'کارشناسی ارشد', 'دکتری']),
                    education_field='زبان انگلیسی',
                    experience_years=random.choice([3, 5, 8, 10, 12]),
                    telegram_username=f'test_teacher{i+1}',
                    whatsapp_number=random_phone(),
                )
                teachers.append(teacher_profile)

        # Create categories
        self.stdout.write(self.style.SUCCESS('Creating categories...'))
        base_categories = [
            ('مکالمه', 'conversation', 'انگلیسی'),
            ('گرامر', 'grammar', 'انگلیسی'),
            ('IELTS', 'ielts', 'انگلیسی'),
            ('کودکان', 'kids', 'انگلیسی'),
            ('واژگان', 'vocabulary', 'انگلیسی'),
            ('انگلیسی تجاری', 'business', 'انگلیسی'),
            ('آمادگی تافل', 'toefl', 'انگلیسی'),
            ('مکالمه پیشرفته', 'advanced_conversation', 'انگلیسی'),
        ]
        categories = []
        for name, key, lang in base_categories:
            category, _ = Category.objects.get_or_create(
                name=name,
                defaults={
                    'description': f'دسته‌بندی {name} برای زبان‌آموزان در سطح‌های مختلف',
                    'language': 'english',
                    'is_active': True,
                }
            )
            categories.append(category)

        # Create courses
        self.stdout.write(self.style.SUCCESS('Creating courses...'))
        courses = []
        level_choices = ['beginner', 'intermediate', 'advanced']
        age_choices = ['kids', 'teens', 'adults']
        class_types = ['general', 'grammar', 'writing', 'speaking', 'listening', 'reading', 'vocabulary', 'conversation', 'exam', 'ielts', 'toefl']
        
        course_titles = [
            'دوره مکالمه مبتدی', 'دوره گرامر متوسط', 'آمادگی آیلتس', 'انگلیسی کودکان',
            'دوره واژگان پیشرفته', 'مکالمه تجاری', 'آمادگی تافل', 'انگلیسی نوجوانان',
            'دوره شنیداری', 'دوره نوشتاری', 'انگلیسی عمومی', 'مکالمه پیشرفته'
        ]

        for i in range(num_courses):
            teacher = random.choice(teachers) if teachers else None
            category = random.choice(categories) if categories else None
            title = f"{random.choice(course_titles)} - سطح {random.choice(['1', '2', '3', '4'])} - {random_string(4)}"
            price = random.choice([0, 200000, 300000, 400000, 500000, 600000, 800000, 1000000])
            is_free = price == 0
            start_delta = random.randint(-30, 60)
            start_date = date.today() + timedelta(days=start_delta)
            duration_options = [
                'شنبه-سه‌شنبه 18:00-19:30',
                'دوشنبه-پنج‌شنبه 10:00-11:30',
                'یکشنبه‌ها 16:00-18:00',
                'چهارشنبه‌ها 14:00-16:00',
                'جمعه‌ها 10:00-12:00'
            ]

            course = Course.objects.create(
                status=random.choices(['draft', 'published'], weights=[1, 4])[0],
                title=title,
                description='این دوره برای بهبود مهارت‌های زبان انگلیسی طراحی شده است و شامل تمرین‌های عملی و تعاملی می‌باشد.',
                short_description='مرور سریع سرفصل‌ها و اهداف دوره.',
                teacher=teacher,
                category=category,
                start_date=start_date,
                end_date=start_date + timedelta(days=random.choice([30, 45, 60, 90])),
                duration=random.choice(duration_options),
                class_time=random.choice(['90 دقیقه', '120 دقیقه', '60 دقیقه']),
                total_hours=random.choice([8, 10, 12, 16, 20, 24, 30]),
                level=random.choice(level_choices),
                age_group=random.choice(age_choices),
                class_type=random.choice(class_types),
                capacity=random.choice([8, 10, 12, 15, 20, 25]),
                price=price,
                location=random.choice(['آنلاین', 'شعبه ونک', 'شعبه تجریش', 'شعبه پاسداران']),
                is_active=True,
                is_free=is_free,
                is_featured=random.choice([True, False, False, False]),  # 1/4 chance
                is_online=random.choice([True, False]),
            )
            courses.append(course)

        # Create enrollments (only for published courses)
        self.stdout.write(self.style.SUCCESS('Creating enrollments...'))
        published_courses = [c for c in courses if c.status == 'published']
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

            status = random.choices(['pending', 'confirmed', 'completed', 'cancelled'], weights=[2, 6, 1, 1])[0]
            payment_status = 'paid' if status in ['confirmed', 'completed'] and course.price > 0 else random.choice(['unpaid', 'partial'])
            amount_paid = 0
            if payment_status == 'paid':
                amount_paid = int(course.price)
            elif payment_status == 'partial' and course.price:
                amount_paid = int(course.price) // random.choice([2, 3])

            Enrollment.objects.create(
                student=student,
                course=course,
                status=status,
                payment_status=payment_status,
                enrolled_at=timezone.now() - timedelta(days=random.randint(0, 30)),
                note=random.choice(['', 'درخواست تغییر زمان کلاس', 'تماس تلفنی برای هماهنگی', '']),
                amount_paid=amount_paid,
                discount_applied=random.choice([0, 0, 50000, 100000]),
                enrollment_source=random.choice(['website', 'phone', 'in_person', 'referral', 'social_media']),
                completion_percentage=0 if status in ['pending', 'confirmed'] else random.choice([50, 80, 100]),
            )

        # Create contact-related requests
        self.stdout.write(self.style.SUCCESS('Creating advice/determination/collaboration/course requests...'))
        for i in range(num_requests):
            first_name, last_name = persian_names[i % len(persian_names)]
            
            AdviceRequest.objects.create(
                name=f"{first_name} {last_name}",
                email=f"test_advice{i+1}@example.com",
                phone=random_phone(),
                message=f"نیاز به مشاوره در مورد انتخاب دوره مناسب دارم. علاقه‌مند به {random.choice(['مکالمه', 'آیلتس', 'انگلیسی تجاری', 'انگلیسی کودکان'])} هستم.",
                submitted_at=timezone.now() - timedelta(days=random.randint(0, 20)),
            )
            
            DeterminationRequest.objects.create(
                name=f"{first_name} {last_name}",
                email=f"test_placement{i+1}@example.com",
                phone=random_phone(),
                message=f"درخواست تعیین سطح آنلاین دارم. قبلاً {random.choice(['مبتدی', 'متوسط', 'پیشرفته'])} بوده‌ام.",
                submitted_at=timezone.now() - timedelta(days=random.randint(0, 20)),
            )
            
            CollabrateRequest.objects.create(
                name=f"{first_name} {last_name}",
                email=f"test_collab{i+1}@example.com",
                phone=random_phone(),
                message=f"تمایل به همکاری به عنوان مدرس دارم. تخصص در {random.choice(['IELTS', 'مکالمه', 'گرامر', 'انگلیسی کودکان'])} دارم.",
                submitted_at=timezone.now() - timedelta(days=random.randint(0, 20)),
                status=random.choice(['pending', 'approved', 'rejected']),
            )
            
            RequestCourse.objects.create(
                name=f"{first_name} {last_name}",
                email=f"test_request{i+1}@example.com",
                phone=random_phone(),
                course_title=f"درخواست دوره {random.choice(['IELTS', 'مکالمه', 'گرامر', 'انگلیسی کودکان'])} سطح {random.choice(['A1', 'A2', 'B1', 'B2'])}",
                description=f"توضیحات تکمیلی برای درخواست دوره. ترجیح {random.choice(['آنلاین', 'حضوری', 'ترکیبی'])} است.",
                created_at=timezone.now() - timedelta(days=random.randint(0, 20)),
            )

        self.stdout.write(self.style.SUCCESS('Test data addition completed successfully!'))
        self.stdout.write(self.style.SUCCESS(f'Added: {len(students)} students, {len(teachers)} teachers, {len(courses)} courses, {num_enrollments} enrollments, {num_requests} requests each type'))
