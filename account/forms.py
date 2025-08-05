from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Student, Teacher, TeacherApplication
import re

User = get_user_model()


class StudentRegistrationForm(UserCreationForm):
    """Registration form for students"""
    
    first_name = forms.CharField(
        max_length=30,
        label='نام',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خود را وارد کنید'})
    )
    last_name = forms.CharField(
        max_length=30,
        label='نام خانوادگی',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی خود را وارد کنید'})
    )
    email = forms.EmailField(
        label='آدرس ایمیل',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'})
    )
    phone_number = forms.CharField(
        max_length=20,
        label='شماره تلفن',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09123456789'})
    )
    
    password1 = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور خود را وارد کنید'})
    )
    password2 = forms.CharField(
        label='تایید رمز عبور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور خود را مجدد وارد کنید'})
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'student'
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create student profile
            Student.objects.create(
                user=user,
                phone_number=self.cleaned_data.get('phone_number', '')
            )
        return user


class TeacherRegistrationForm(UserCreationForm):
    """Registration form for teachers (only allowed after application acceptance)"""
    
    first_name = forms.CharField(
        max_length=30,
        label='نام',
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True})
    )
    last_name = forms.CharField(
        max_length=30,
        label='نام خانوادگی',
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True})
    )
    email = forms.EmailField(
        label='آدرس ایمیل',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'readonly': True})
    )
    
    password1 = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور خود را وارد کنید'})
    )
    password2 = forms.CharField(
        label='تایید رمز عبور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور خود را مجدد وارد کنید'})
    )
    
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'درباره خود بنویسید...'}),
        label='بیوگرافی',
        required=False
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        self.application = kwargs.pop('application', None)
        super().__init__(*args, **kwargs)
        
        if self.application:
            self.fields['first_name'].initial = self.application.first_name
            self.fields['last_name'].initial = self.application.last_name
            self.fields['email'].initial = self.application.email
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if not self.application or self.application.email != email:
            raise ValidationError('شما تنها می‌توانید با ایمیل تایید شده ثبت‌نام کنید.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'teacher'
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create teacher profile
            Teacher.objects.create(
                user=user,
                application=self.application,
                bio=self.cleaned_data.get('bio', ''),
                specialties=self.application.specialties
            )
        return user


class CustomLoginForm(AuthenticationForm):
    """Custom login form using email instead of username"""
    
    username = forms.EmailField(
        label='آدرس ایمیل',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'آدرس ایمیل خود را وارد کنید'})
    )
    password = forms.CharField(
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور خود را وارد کنید'})
    )
    
    error_messages = {
        'invalid_login': 'ایمیل یا رمز عبور اشتباه است.',
        'inactive': 'این حساب کاربری غیرفعال است.',
    }


class TeacherApplicationForm(forms.ModelForm):
    """Form for teacher application submission"""
    
    class Meta:
        model = TeacherApplication
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'education', 'experience', 'certifications', 'specialties',
            'motivation', 'cv_file'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '09123456789'}),
            'education': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'مدارک تحصیلی و رشته تحصیلی خود را شرح دهید...'}),
            'experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'سوابق تدریس و تجربیات کاری خود را توضیح دهید...'}),
            'certifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'گواهینامه‌ها و مدارک مرتبط (اختیاری)'}),
            'specialties': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'تخصص‌های شما در تدریس زبان انگلیسی'}),
            'motivation': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'چرا می‌خواهید با ما همکاری کنید؟'}),
            'cv_file': forms.FileInput(attrs={'class': 'form-control-file'}),
        }
        labels = {
            'first_name': 'نام',
            'last_name': 'نام خانوادگی',
            'email': 'آدرس ایمیل',
            'phone_number': 'شماره تلفن',
            'education': 'تحصیلات',
            'experience': 'تجربه تدریس',
            'certifications': 'گواهینامه‌ها',
            'specialties': 'تخصص‌ها',
            'motivation': 'انگیزه همکاری',
            'cv_file': 'فایل رزومه (اختیاری)',
        }
    
    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        # Basic Iranian phone number validation
        if phone and not re.match(r'^09\d{9}$', phone):
            raise ValidationError('شماره تلفن باید با 09 شروع شده و 11 رقم باشد.')
        return phone
    
    def clean_email(self):
        email = self.cleaned_data['email']
        # Check if email already has a pending or accepted application
        if TeacherApplication.objects.filter(email=email, status__in=['pending', 'accepted']).exists():
            raise ValidationError('با این ایمیل قبلاً درخواست ارسال شده است.')
        return email


class StudentProfileForm(forms.ModelForm):
    """Form for updating student profile"""
    
    class Meta:
        model = Student
        fields = ['phone_number', 'date_of_birth', 'address', 'english_level', 'goals']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'english_level': forms.Select(attrs={'class': 'form-control'}),
            'goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
        labels = {
            'phone_number': 'شماره تلفن',
            'date_of_birth': 'تاریخ تولد',
            'address': 'آدرس',
            'english_level': 'سطح زبان انگلیسی',
            'goals': 'اهداف یادگیری',
        }


class TeacherProfileForm(forms.ModelForm):
    """Form for updating teacher profile"""
    
    class Meta:
        model = Teacher
        fields = ['bio', 'specialties', 'hourly_rate']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'specialties': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'bio': 'بیوگرافی',
            'specialties': 'تخصص‌ها',
            'hourly_rate': 'نرخ ساعتی (تومان)',
        } 