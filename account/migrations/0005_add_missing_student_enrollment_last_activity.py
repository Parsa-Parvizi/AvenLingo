from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0004_add_missing_student_goals'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='enrollment_date',
            field=models.DateTimeField(
                verbose_name='تاریخ ثبت‌نام',
                default=django.utils.timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='student',
            name='last_activity',
            field=models.DateTimeField(
                verbose_name='آخرین فعالیت',
                auto_now=True,
            ),
            preserve_default=False,
        ),
    ] 