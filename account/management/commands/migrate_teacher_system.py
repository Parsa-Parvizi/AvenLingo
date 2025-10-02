"""
Management command to migrate from old collaboration system to new teacher application system.
This command helps clean up the database and ensures data consistency.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from account.models import TeacherApplication, User, Teacher


class Command(BaseCommand):
    help = 'Migrate from old collaboration system to new teacher application system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--cleanup-duplicates',
            action='store_true',
            help='Clean up duplicate applications with same email',
        )
        parser.add_argument(
            '--fix-expired',
            action='store_true',
            help='Mark expired applications that have passed expiry date',
        )
        parser.add_argument(
            '--validate-system',
            action='store_true',
            help='Validate the integrity of the teacher application system',
        )
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('Running in DRY RUN mode - no changes will be made')
            )
        
        try:
            if options['cleanup_duplicates']:
                self.cleanup_duplicate_applications()
            
            if options['fix_expired']:
                self.fix_expired_applications()
            
            if options['validate_system']:
                self.validate_system_integrity()
            
            if not any([options['cleanup_duplicates'], options['fix_expired'], options['validate_system']]):
                self.stdout.write('No specific action requested. Use --help to see available options.')
                
        except Exception as e:
            raise CommandError(f'Error during migration: {str(e)}')
    
    def cleanup_duplicate_applications(self):
        """Clean up duplicate teacher applications with the same email"""
        self.stdout.write('Checking for duplicate teacher applications...')
        
        # Find duplicate emails
        from django.db.models import Count
        duplicates = (
            TeacherApplication.objects
            .values('email')
            .annotate(count=Count('email'))
            .filter(count__gt=1)
        )
        
        total_duplicates = 0
        
        for duplicate in duplicates:
            email = duplicate['email']
            applications = TeacherApplication.objects.filter(email=email).order_by('submitted_at')
            
            # Keep the latest application, mark others as duplicates
            latest_app = applications.last()
            older_apps = applications.exclude(id=latest_app.id)
            
            self.stdout.write(f'Found {older_apps.count()} duplicate applications for {email}')
            
            if not self.dry_run:
                with transaction.atomic():
                    for app in older_apps:
                        app.status = 'rejected'
                        app.admin_notes = f'Duplicate application - superseded by application {latest_app.id}'
                        app.reviewed_at = timezone.now()
                        app.save()
                        total_duplicates += 1
            else:
                total_duplicates += older_apps.count()
        
        if total_duplicates > 0:
            action = 'Would mark' if self.dry_run else 'Marked'
            self.stdout.write(
                self.style.SUCCESS(f'{action} {total_duplicates} duplicate applications as rejected')
            )
        else:
            self.stdout.write(self.style.SUCCESS('No duplicate applications found'))
    
    def fix_expired_applications(self):
        """Mark applications as expired if they have passed their expiry date"""
        self.stdout.write('Checking for expired applications...')
        
        now = timezone.now()
        expired_apps = TeacherApplication.objects.filter(
            status='accepted',
            expires_at__lt=now
        )
        
        count = expired_apps.count()
        
        if count > 0:
            if not self.dry_run:
                with transaction.atomic():
                    expired_apps.update(
                        status='expired',
                        admin_notes='Application expired - registration period exceeded'
                    )
            
            action = 'Would mark' if self.dry_run else 'Marked'
            self.stdout.write(
                self.style.SUCCESS(f'{action} {count} applications as expired')
            )
        else:
            self.stdout.write(self.style.SUCCESS('No expired applications found'))
    
    def validate_system_integrity(self):
        """Validate the integrity of the teacher application system"""
        self.stdout.write('Validating system integrity...')
        
        issues = []
        
        # Check for teachers without applications
        teachers_without_apps = Teacher.objects.filter(application__isnull=True)
        if teachers_without_apps.exists():
            issues.append(f'{teachers_without_apps.count()} teachers found without linked applications')
        
        # Check for accepted applications without teachers
        accepted_apps_without_teachers = TeacherApplication.objects.filter(
            status='accepted',
            teacher_account__isnull=True,
            expires_at__gt=timezone.now()
        )
        if accepted_apps_without_teachers.exists():
            issues.append(f'{accepted_apps_without_teachers.count()} accepted applications found without teacher accounts')
        
        # Check for users with teacher type but no teacher profile
        teacher_users_without_profile = User.objects.filter(
            user_type='teacher',
            teacher_profile__isnull=True
        )
        if teacher_users_without_profile.exists():
            issues.append(f'{teacher_users_without_profile.count()} teacher users found without teacher profiles')
        
        # Check for applications with invalid statuses
        invalid_status_apps = TeacherApplication.objects.exclude(
            status__in=['pending', 'accepted', 'rejected', 'expired']
        )
        if invalid_status_apps.exists():
            issues.append(f'{invalid_status_apps.count()} applications with invalid status found')
        
        # Check for applications without proper review data
        reviewed_apps_without_reviewer = TeacherApplication.objects.filter(
            status__in=['accepted', 'rejected'],
            reviewed_by__isnull=True
        )
        if reviewed_apps_without_reviewer.exists():
            issues.append(f'{reviewed_apps_without_reviewer.count()} reviewed applications without reviewer info')
        
        if issues:
            self.stdout.write(self.style.ERROR('System integrity issues found:'))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f'  - {issue}'))
            
            if not self.dry_run:
                self.stdout.write(
                    self.style.WARNING('Run with specific fix commands to resolve these issues')
                )
        else:
            self.stdout.write(self.style.SUCCESS('System integrity validation passed'))
        
        # Statistics
        self.print_statistics()
    
    def print_statistics(self):
        """Print system statistics"""
        self.stdout.write('\n--- System Statistics ---')
        
        # Applications by status
        self.stdout.write('Teacher Applications:')
        for status, display in TeacherApplication.STATUS_CHOICES:
            count = TeacherApplication.objects.filter(status=status).count()
            self.stdout.write(f'  {display}: {count}')
        
        # Users by type
        self.stdout.write('\nUsers by type:')
        for user_type, display in User.USER_TYPE_CHOICES:
            count = User.objects.filter(user_type=user_type).count()
            self.stdout.write(f'  {display}: {count}')
        
        # Teachers
        total_teachers = Teacher.objects.count()
        active_teachers = Teacher.objects.filter(is_active=True).count()
        verified_teachers = Teacher.objects.filter(is_verified=True).count()
        
        self.stdout.write('\nTeachers:')
        self.stdout.write(f'  Total: {total_teachers}')
        self.stdout.write(f'  Active: {active_teachers}')
        self.stdout.write(f'  Verified: {verified_teachers}')
        
        # Students
        from account.models import Student
        total_students = Student.objects.count()
        self.stdout.write(f'\nStudents: {total_students}')
        
        self.stdout.write('--- End Statistics ---\n') 