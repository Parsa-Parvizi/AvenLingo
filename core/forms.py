from django import forms
from .models import AdviceRequest, DeterminationRequest, CollabrateRequest, RequestCourse


class AdviceRequestForm(forms.ModelForm):
    class Meta:
        model = AdviceRequest
        fields = ['name', 'email', 'phone', 'message']
        labels = {
            'name': 'نام و نام خانوادگی',
            'email': 'ایمیل',
            'phone': 'شماره تماس',
            'message': 'متن درخواست مشاوره',
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'placeholder': 'نام و نام خانوادگی'})
        self.fields['email'].widget.attrs.update({'placeholder': 'ایمیل'})
        self.fields['phone'].widget.attrs.update({'placeholder': 'شماره تماس'})
        self.fields['message'].widget.attrs.update({'placeholder': 'متن درخواست مشاوره'})


class DeterminationRequestForm(forms.ModelForm):
    class Meta:
        model = DeterminationRequest
        fields = ['name', 'email', 'phone', 'message']
        labels = {
            'name': 'نام و نام خانوادگی',
            'email': 'ایمیل',
            'phone': 'شماره تماس',
            'message': 'متن درخواست تعیین سطح',
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'placeholder': 'نام و نام خانوادگی'})
        self.fields['email'].widget.attrs.update({'placeholder': 'ایمیل'})
        self.fields['phone'].widget.attrs.update({'placeholder': 'شماره تماس'})
        self.fields['message'].widget.attrs.update({'placeholder': 'متن درخواست تعیین سطح'})


class CollabrateRequestForm(forms.ModelForm):
    class Meta:
        model = CollabrateRequest
        fields = ['name', 'email', 'phone', 'message']
        labels = {
            'name': 'نام و نام خانوادگی',
            'email': 'ایمیل',
            'phone': 'شماره تماس',
            'message': 'متن درخواست همکاری',
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'placeholder': 'نام و نام خانوادگی'})
        self.fields['email'].widget.attrs.update({'placeholder': 'ایمیل'})
        self.fields['phone'].widget.attrs.update({'placeholder': 'شماره تماس'})
        self.fields['message'].widget.attrs.update({'placeholder': 'متن درخواست همکاری'})

class RequestCourseForm(forms.ModelForm):
    class Meta:
        model = RequestCourse
        fields = ['name', 'email', 'phone', 'course_title', 'description']