import uuid
from django.db import models
from django.conf import settings


class Teacher(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='teacher_profile_old')
    full_name = models.CharField(max_length=100,  null=True, blank=True)

    bio = models.TextField("بیوگرافی", blank=True)
    expertise = models.CharField("تخصص", max_length=100, blank=True)
    phone_number = models.CharField("شماره تماس", max_length=20, blank=True)
    image = models.ImageField(upload_to='teachers/', null=True, blank=True)

    linkedin = models.URLField("لینکدین", blank=True)
    instagram = models.URLField("اینستاگرام", blank=True)
    website = models.URLField("وب‌سایت شخصی", blank=True)

    is_active = models.BooleanField(default=True) #type: ignore

    REGISTRATION_STATUS_CHOICES = [
        ("pending", "در انتظار تایید"),
        ("approved", "تایید شده توسط ادمین"),
        ("registered", "ثبت‌نام کامل شده"),
    ]
    registration_status = models.CharField(
        max_length=20,
        choices=REGISTRATION_STATUS_CHOICES,
        default="pending",
        verbose_name="وضعیت ثبت‌نام"
    )

    def __str__(self):
        return f"{self.user.get_full_name()}" #type: ignore

    class Meta:
        verbose_name = "مدرس"
        verbose_name_plural = "مدرسان"