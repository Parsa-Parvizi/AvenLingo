# Generated manually to fix teacher_id field type mismatch

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('course', '0004_add_missing_fields'),
        ('teacher', '0001_initial'),
    ]

    operations = [
        # First, remove the old foreign key constraint
        migrations.RemoveField(
            model_name='course',
            name='teacher',
        ),
        
        # Add the correct teacher field with UUID type
        migrations.AddField(
            model_name='course',
            name='teacher',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='courses',
                to='teacher.teacher',
                verbose_name='مدرس'
            ),
        ),
    ] 