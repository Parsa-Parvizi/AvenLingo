from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('account', '0006_alter_student_enrollment_date'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE account_student DROP COLUMN IF EXISTS user_id CASCADE;"
                "ALTER TABLE account_student ADD COLUMN user_id uuid NOT NULL;"
                "ALTER TABLE account_student ADD CONSTRAINT account_student_user_id_fk FOREIGN KEY (user_id) REFERENCES account_user(id) DEFERRABLE INITIALLY DEFERRED;"
            ),
            reverse_sql=(
                "ALTER TABLE account_student DROP CONSTRAINT IF EXISTS account_student_user_id_fk;"
                "ALTER TABLE account_student DROP COLUMN IF EXISTS user_id CASCADE;"
                "ALTER TABLE account_student ADD COLUMN user_id integer NOT NULL;"
            ),
        ),
    ] 