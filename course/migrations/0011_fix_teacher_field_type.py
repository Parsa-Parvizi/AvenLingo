# Generated manually to fix teacher field type mismatch

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0014_remove_student_slug'),
        ('course', '0010_course_class_time'),
    ]

    operations = [
        # First, remove the existing teacher field with wrong type
        migrations.RemoveField(
            model_name='course',
            name='teacher',
        ),
        
        # Add the correct teacher field with bigint type pointing to account.Teacher
        migrations.AddField(
            model_name='course',
            name='teacher',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='courses',
                to='account.teacher',
                verbose_name='مدرس'
            ),
        ),
    ] 