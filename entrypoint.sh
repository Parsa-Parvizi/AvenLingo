#!/bin/bash
set -e

echo "🚀 Starting English Teacher Academy Django Application..."

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
python manage.py check --database default

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "👤 Creating superuser (if needed)..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@academy.com').exists():
    User.objects.create_superuser(
        email='admin@academy.com',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print('✅ Superuser created: admin@academy.com / admin123')
else:
    print('ℹ️  Superuser already exists')
" || echo "⚠️  Superuser creation skipped"

# Collect static files in production
if [ "$DJANGO_DEBUG" != "True" ]; then
    echo "📦 Collecting static files..."
    python manage.py collectstatic --noinput --clear
fi

# Start the application
echo "🎯 Starting Django application on port 8000..."
exec "$@" 