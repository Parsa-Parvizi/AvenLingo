from django.contrib.auth.models import AnonymousUser


def is_student(user):
    return bool(user and not isinstance(user, AnonymousUser) and getattr(user, 'user_type', None) == 'student')


def is_teacher(user):
    return bool(user and not isinstance(user, AnonymousUser) and getattr(user, 'user_type', None) == 'teacher') 