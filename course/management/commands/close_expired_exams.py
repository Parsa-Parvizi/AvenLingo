from django.core.management.base import BaseCommand
from django.utils import timezone
from course.models import Exam, ExamParticipation


class Command(BaseCommand):
    help = 'بسته کردن خودکار امتحانات منقضی شده'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        
        # پیدا کردن امتحاناتی که باید بسته شوند
        exams_to_close = Exam.objects.filter(
            scheduled_end__lte=now,
            status__in=['scheduled', 'active'],
            auto_close=True
        )
        
        closed_count = 0
        submitted_count = 0
        
        for exam in exams_to_close:
            # تغییر وضعیت امتحان
            exam.status = 'ended'
            exam.save()
            closed_count += 1
            
            # ارسال خودکار شرکت‌های شروع شده اما ارسال نشده
            started_participations = ExamParticipation.objects.filter(
                exam=exam,
                status='started'
            )
            
            for participation in started_participations:
                participation.status = 'submitted'
                participation.submitted_at = now
                participation.is_late = True
                participation.save()
                submitted_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ امتحان "{exam.title}" بسته شد. '
                    f'{started_participations.count()} شرکت به صورت خودکار ارسال شد.'
                )
            )
        
        # فعال کردن خودکار امتحانات که زمان شروع آن‌ها رسیده
        exams_to_activate = Exam.objects.filter(
            scheduled_start__lte=now,
            scheduled_end__gt=now,
            status='scheduled',
            is_visible=True
        )
        
        activated_count = 0
        for exam in exams_to_activate:
            exam.status = 'active'
            exam.save()
            activated_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'▶️ امتحان "{exam.title}" فعال شد.')
            )
        
        # خلاصه
        if closed_count > 0 or activated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n📊 خلاصه:\n'
                    f'   • {closed_count} امتحان بسته شد\n'
                    f'   • {submitted_count} شرکت خودکار ارسال شد\n'
                    f'   • {activated_count} امتحان فعال شد'
                )
            )
        else:
            self.stdout.write(self.style.WARNING('⚠️  هیچ امتحانی برای بستن یا فعال‌سازی یافت نشد.'))
