from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_alter_authsystemsettings_instagram_url_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='goals',
            field=models.TextField(
                verbose_name='اهداف یادگیری',
                blank=True,
                default='',
            ),
            preserve_default=False,
        ),
    ] 