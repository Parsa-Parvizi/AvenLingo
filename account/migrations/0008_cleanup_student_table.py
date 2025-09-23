from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('account', '0007_alter_student_user_to_uuid'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE account_student DROP COLUMN IF EXISTS is_active;"
                "ALTER TABLE account_student DROP COLUMN IF EXISTS first_login_at;"
                "ALTER TABLE account_student DROP COLUMN IF EXISTS last_login_at;"
            ),
            reverse_sql=(
                "ALTER TABLE account_student ADD COLUMN is_active boolean NOT NULL DEFAULT TRUE;"
                "ALTER TABLE account_student ADD COLUMN first_login_at timestamp with time zone NULL;"
                "ALTER TABLE account_student ADD COLUMN last_login_at timestamp with time zone NULL;"
            ),
        ),
    ] 