from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_alter_sitesettings_developer_link'),
        ('account', '0008_cleanup_student_table'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                """
                DELETE FROM django_admin_log;
                DO $$
                DECLARE r RECORD;
                BEGIN
                    FOR r IN (
                        SELECT conname FROM pg_constraint
                        WHERE conrelid = 'django_admin_log'::regclass
                          AND contype = 'f'
                    ) LOOP
                        EXECUTE 'ALTER TABLE django_admin_log DROP CONSTRAINT ' || quote_ident(r.conname) || ';';
                    END LOOP;
                END $$;
                ALTER TABLE django_admin_log ALTER COLUMN user_id DROP NOT NULL;
                ALTER TABLE django_admin_log ALTER COLUMN user_id TYPE uuid USING NULL;
                """
            ),
            reverse_sql=(
                """
                ALTER TABLE django_admin_log ALTER COLUMN user_id TYPE integer USING NULL;
                """
            ),
        ),
    ] 