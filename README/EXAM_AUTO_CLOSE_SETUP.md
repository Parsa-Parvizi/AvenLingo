# تنظیم Auto-Close برای امتحانات

## روش 1: Cron Job (توصیه می‌شود)

برای اجرای خودکار بسته شدن امتحانات هر دقیقه:

```bash
# باز کردن crontab
crontab -e

# اضافه کردن این خط:
* * * * * cd /home/codus/EnglishTeacherMobina && /home/codus/EnglishTeacherMobina/venv/bin/python manage.py close_expired_exams >> /var/log/exam_close.log 2>&1
```

## روش 2: اجرای دستی

```bash
python manage.py close_expired_exams
```

## روش 3: Celery (برای production)

اگر Celery دارید، می‌توانید یک periodic task تعریف کنید:

```python
# در celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('EnglishTeacher')

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # هر دقیقه
    sender.add_periodic_task(60.0, close_exams.s(), name='close expired exams')

@app.task
def close_exams():
    from django.core.management import call_command
    call_command('close_expired_exams')
```

## عملکرد Command:

1. ✅ امتحاناتی که زمان پایان آن‌ها رسیده را می‌بندد
2. ✅ شرکت‌های شروع شده اما ارسال نشده را خودکار ارسال می‌کند
3. ✅ امتحانات زمان‌بندی شده که زمان شروعشان رسیده را فعال می‌کند
4. ✅ لاگ کامل از عملیات

## تست:

```bash
# ایجاد یک امتحان تست با زمان پایان 1 دقیقه آینده
# بعد از 1 دقیقه:
python manage.py close_expired_exams

# خروجی باید نشان دهد که امتحان بسته شد
```
