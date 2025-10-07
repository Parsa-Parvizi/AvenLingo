from django import forms
from .models import AdviceRequest, DeterminationRequest, RequestCourse, CollabrateRequest, ContactMessage, PrivateClassRequest


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
            'resume': 'رزومه',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام و نام خانوادگی'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'آدرس ایمیل'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شماره تماس'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'توضیحات و انگیزه همکاری'
            }),
            'resume': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            })
        }
    
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
        labels = {
            'name': 'نام و نام خانوادگی',
            'email': 'ایمیل',
            'phone': 'شماره تماس',
            'course_title': 'عنوان دوره پیشنهادی',
            'description': 'توضیحات تکمیلی',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام و نام خانوادگی'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'آدرس ایمیل'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شماره تماس'
            }),
            'course_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان دوره‌ای که می‌خواهید'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'توضیحات بیشتر درباره دوره مورد نظر'
            })
        }


class ContactMessageForm(forms.ModelForm):
    """فرم تماس با ما"""
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        labels = {
            'name': 'نام و نام خانوادگی',
            'email': 'ایمیل',
            'phone': 'شماره تماس',
            'subject': 'موضوع پیام',
            'message': 'متن پیام',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام و نام خانوادگی خود را وارد کنید',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'آدرس ایمیل خود را وارد کنید',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '09123456789',
                'pattern': '[0-9]{11}',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'موضوع پیام خود را بنویسید',
                'required': True
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'پیام خود را اینجا بنویسید...',
                'required': True
            })
        }
    
    def clean_phone(self):
        """اعتبارسنجی شماره تلفن"""
        phone = self.cleaned_data.get('phone')
        if phone and not phone.isdigit():
            raise forms.ValidationError('شماره تلفن باید فقط شامل اعداد باشد.')
        if phone and len(phone) != 11:
            raise forms.ValidationError('شماره تلفن باید 11 رقم باشد.')
        return phone


class PrivateClassRequestForm(forms.ModelForm):
    """فرم درخواست کلاس خصوصی"""
    class Meta:
        model = PrivateClassRequest
        fields = ['name', 'email', 'phone', 'current_level', 'preferred_time', 'goals', 'additional_info']
        labels = {
            'name': 'نام و نام خانوادگی',
            'email': 'ایمیل',
            'phone': 'شماره تماس',
            'current_level': 'سطح فعلی زبان انگلیسی شما',
            'preferred_time': 'زمان ترجیحی برگزاری کلاس',
            'goals': 'اهداف و نیازهای شما از یادگیری زبان',
            'additional_info': 'توضیحات تکمیلی',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام و نام خانوادگی خود را وارد کنید',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'آدرس ایمیل خود را وارد کنید',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '09123456789',
                'pattern': '[0-9]{11}',
                'required': True
            }),
            'current_level': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'preferred_time': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: عصرها، آخر هفته‌ها، صبح‌ها'
            }),
            'goals': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'لطفاً اهداف خود از یادگیری زبان را توضیح دهید. مثال: آمادگی برای آیلتس، مکالمه روزمره، پیشرفت شغلی',
                'required': True
            }),
            'additional_info': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'هر اطلاعات اضافی که فکر می‌کنید برای ما مفید است'
            })
        }
    
    def clean_phone(self):
        """اعتبارسنجی شماره تلفن"""
        phone = self.cleaned_data.get('phone')
        if phone and not phone.isdigit():
            raise forms.ValidationError('شماره تلفن باید فقط شامل اعداد باشد.')
        if phone and len(phone) != 11:
            raise forms.ValidationError('شماره تلفن باید 11 رقم باشد.')
        return phone