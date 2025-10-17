"""
دستور مدیریتی برای همگام‌سازی وضعیت ثبت‌نام و پرداخت
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from enrollment.models import Enrollment


class Command(BaseCommand):
    help = 'همگام‌سازی وضعیت ثبت‌نام و پرداخت برای تمام ثبت‌نام‌ها'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='اصلاح خودکار ثبت‌نام‌های ناهماهنگ',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='فقط نمایش مشکلات بدون اصلاح',
        )

    def handle(self, *args, **options):
        fix = options.get('fix', False)
        dry_run = options.get('dry_run', False)
        
        self.stdout.write(self.style.SUCCESS('🔍 در حال بررسی ثبت‌نام‌ها...'))
        
        # تمام ثبت‌نام‌ها
        all_enrollments = Enrollment.objects.select_related('course', 'student').all()
        
        issues_found = 0
        fixed_count = 0
        
        for enrollment in all_enrollments:
            has_issue = False
            issue_type = ""
            
            # دوره‌های رایگان
            if enrollment.course.is_free:
                if enrollment.status == 'confirmed' and enrollment.payment_status != 'paid':
                    has_issue = True
                    issue_type = "رایگان - پرداخت تنظیم نشده"
                    
                    if fix and not dry_run:
                        enrollment.payment_status = 'paid'
                        enrollment.amount_paid = 0
                        enrollment.save()
                        fixed_count += 1
            
            # دوره‌های غیر رایگان
            else:
                # ثبت‌نام confirmed ولی پرداخت نه paid و نه partial
                if enrollment.status == 'confirmed' and enrollment.payment_status not in ['paid', 'partial']:
                    has_issue = True
                    issue_type = "ثبت‌نام تایید شده ولی پرداخت نشده"
                    
                    if fix and not dry_run:
                        # برگرداندن به pending
                        enrollment.status = 'pending'
                        enrollment.confirmed_at = None
                        enrollment.save()
                        fixed_count += 1
                
                # پرداخت paid/partial ولی ثبت‌نام pending
                elif enrollment.payment_status in ['paid', 'partial'] and enrollment.status == 'pending':
                    has_issue = True
                    issue_type = "پرداخت تایید شده ولی ثبت‌نام pending"
                    
                    if fix and not dry_run:
                        # تایید خودکار ثبت‌نام
                        enrollment.status = 'confirmed'
                        enrollment.confirmed_at = timezone.now()
                        enrollment.save()
                        fixed_count += 1
            
            if has_issue:
                issues_found += 1
                status_icon = "✅" if (fix and not dry_run) else "⚠️"
                
                self.stdout.write(
                    f"\n{status_icon} ID: {enrollment.id} - {enrollment.student.user.get_full_name()} → {enrollment.course.title}"
                )
                self.stdout.write(f"   مشکل: {issue_type}")
                self.stdout.write(f"   وضعیت ثبت‌نام: {enrollment.get_status_display()}")
                self.stdout.write(f"   وضعیت پرداخت: {enrollment.get_payment_status_display()}")
                self.stdout.write(f"   نوع دوره: {'رایگان' if enrollment.course.is_free else 'غیر رایگان'}")
        
        # خلاصه نتایج
        self.stdout.write("\n" + "="*70)
        
        if issues_found == 0:
            self.stdout.write(self.style.SUCCESS('✅ همه ثبت‌نام‌ها هماهنگ هستند!'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠️  تعداد مشکلات یافت شده: {issues_found}'))
            
            if dry_run:
                self.stdout.write(self.style.NOTICE('ℹ️  برای اصلاح مشکلات، دستور را با پارامتر --fix اجرا کنید'))
            elif fix:
                self.stdout.write(self.style.SUCCESS(f'✅ تعداد اصلاح شده: {fixed_count}'))
            else:
                self.stdout.write(self.style.NOTICE('ℹ️  برای نمایش تغییرات پیشنهادی: --dry-run'))
                self.stdout.write(self.style.NOTICE('ℹ️  برای اصلاح خودکار: --fix'))
        
        self.stdout.write("="*70)

