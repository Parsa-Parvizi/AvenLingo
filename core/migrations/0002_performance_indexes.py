 # Generated for performance optimization

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('course', '0001_initial'),
        ('account', '0001_initial'),
        ('teacher', '0001_initial'),
        ('enrollment', '0002_enrollmenthistory_alter_enrollment_options_and_more'),
    ]

    operations = [
        # Add indexes for core models
        migrations.RunSQL(
            'CREATE INDEX IF NOT EXISTS idx_faq_active_order ON core_faq (is_active, "order");',
            reverse_sql="DROP INDEX IF EXISTS idx_faq_active_order;"
        ),
        migrations.RunSQL(
            'CREATE INDEX IF NOT EXISTS idx_heroslider_active_order ON core_heroslider (is_active, "order");',
            reverse_sql="DROP INDEX IF EXISTS idx_heroslider_active_order;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_testimonial_active_featured ON core_testimonial (is_active, is_featured, created_at);",
            reverse_sql="DROP INDEX IF EXISTS idx_testimonial_active_featured;"
        ),
        
        # Add indexes for course models
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_course_active_featured ON course_course (is_active, is_featured);",
            reverse_sql="DROP INDEX IF EXISTS idx_course_active_featured;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_course_active_created ON course_course (is_active, created_at);",
            reverse_sql="DROP INDEX IF EXISTS idx_course_active_created;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_course_title_search ON course_course (title);",
            reverse_sql="DROP INDEX IF EXISTS idx_course_title_search;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_category_active_name ON course_category (is_active, name);",
            reverse_sql="DROP INDEX IF EXISTS idx_category_active_name;"
        ),
        
        # Add indexes for teacher models
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_teacher_active_status ON teacher_teacher (is_active, registration_status);",
            reverse_sql="DROP INDEX IF EXISTS idx_teacher_active_status;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_teacher_name_search ON teacher_teacher (full_name);",
            reverse_sql="DROP INDEX IF EXISTS idx_teacher_name_search;"
        ),
        
        # Add indexes for account models
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_user_email_type ON account_user (email, user_type);",
            reverse_sql="DROP INDEX IF EXISTS idx_user_email_type;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_user_active_type ON account_user (is_active, user_type);",
            reverse_sql="DROP INDEX IF EXISTS idx_user_active_type;"
        ),
        
        # Add indexes for enrollment models
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_enrollment_status_payment ON enrollment_enrollment (status, payment_status);",
            reverse_sql="DROP INDEX IF EXISTS idx_enrollment_status_payment;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_enrollment_enrolled_at ON enrollment_enrollment (enrolled_at);",
            reverse_sql="DROP INDEX IF EXISTS idx_enrollment_enrolled_at;"
        ),
        
        # Add composite indexes for common queries
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_course_teacher_category ON course_course (teacher_id, category_id, is_active);",
            reverse_sql="DROP INDEX IF EXISTS idx_course_teacher_category;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_enrollment_student_course ON enrollment_enrollment (student_id, course_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_enrollment_student_course;"
        ),
    ]