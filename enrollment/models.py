from django.db import models
from account.models import Student
from course.models import Course


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')

    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_confirmed = models.BooleanField("تأیید شده؟", default=False) #type: ignore
    note = models.TextField("یادداشت", blank=True)

    class Meta:
        unique_together = ('student', 'course')
        verbose_name = "ثبت‌نام"
        verbose_name_plural = "ثبت‌نام‌ها"

    def __str__(self):
        return f"{self.student} → {self.course}"