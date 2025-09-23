from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='english_level',
            field=models.CharField(
                verbose_name='سطح زبان انگلیسی',
                max_length=20,
                blank=True,
                default='',
            ),
            preserve_default=False,
        ),
    ] 