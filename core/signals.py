
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.utils import timezone
from django.db import connection
from .models import Log
import threading

# Helper to get current user from thread local (for admin actions)
_user = threading.local()

def set_current_user(user):
    _user.value = user

def get_current_user():
    return getattr(_user, 'value', None)

def table_exists(table_name):
    """Check if a database table exists"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM information_schema.tables 
                WHERE table_name = %s
            """, [table_name])
            return cursor.fetchone()[0] > 0
    except Exception:
        return False


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_user(getattr(request, 'user', None))
        response = self.get_response(request)

        return response

# Signal for logging saves
@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    if sender == Log:
        return
    
    # Check if the core_log table exists before trying to use it
    if not table_exists('core_log'):
        return
        
    try:
        user = get_current_user()
        model_name = sender.__name__
        if created:
            action = f"ایجاد {model_name} (ID: {instance.pk})"
            level = 'info'
        else:
            action = f"ویرایش {model_name} (ID: {instance.pk})"
            level = 'warning'
        Log.objects.create(
            message=action,
            level=level,
            user=user
        )
    except Exception:
        # Silently fail during migrations to avoid breaking the migration process
        pass

# Signal for logging deletes
@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    if sender == Log:
        return
    
    # Check if the core_log table exists before trying to use it
    if not table_exists('core_log'):
        return
        
    try:
        user = get_current_user()
        model_name = sender.__name__
        action = f"حذف {model_name} (ID: {instance.pk})"
        Log.objects.create(
            message=action,
            level='error',
            user=user
        )
    except Exception:
        # Silently fail during migrations to avoid breaking the migration process
        pass
