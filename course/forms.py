from django import forms
from .models import Course

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        exclude = [
            'teacher', 'students', 'enrolled_count', 'slug', 'is_active', 'is_featured', 'created_at', 'updated_at', 'status'
        ]
        # فقط فیلدهای مورد نیاز معلم برای ثبت کلاس را نمایش بده

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control' 