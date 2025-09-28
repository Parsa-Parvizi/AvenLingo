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
        fields = ['name', 'email', 'phone', 'message', 'resume']
        labels = {
            'name': 'نام و نام خانوادگی',
            'email': 'آدرس ایمیل',
            'phone': 'شماره تماس',
            'message': 'متن درخواست همکاری',
            'resume': 'رزومه (PDF)',
        }
        widgets = {
            'resume': forms.FileInput(attrs={
                'accept': '.pdf',
                'class': 'form-control',
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({
            'placeholder': 'نام و نام خانوادگی',
            'class': 'form-control'
        })
        self.fields['email'].widget.attrs.update({
            'placeholder': 'آدرس ایمیل',
            'class': 'form-control'
        })
        self.fields['phone'].widget.attrs.update({
            'placeholder': 'شماره تماس',
            'class': 'form-control'
        })
        self.fields['message'].widget.attrs.update({
            'placeholder': 'توضیحات و انگیزه همکاری',
            'class': 'form-control',
            'rows': 4
        })
        self.fields['resume'].widget.attrs.update({
            'class': 'form-control',
            'accept': '.pdf'
        })
    
    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            # بررسی نوع فایل
            if not resume.name.lower().endswith('.pdf'):
                raise forms.ValidationError('فقط فایل‌های PDF مجاز هستند.')
            
            # بررسی حجم فایل (5 مگابایت)
            if resume.size > 5 * 1024 * 1024:
                raise forms.ValidationError('حجم فایل نباید بیشتر از 5 مگابایت باشد.')
        
        return resume

class RequestCourseForm(forms.ModelForm):
    class Meta:
        model = RequestCourse
        fields = ['name', 'email', 'phone', 'course_title', 'description']