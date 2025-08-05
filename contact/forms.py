from django import forms
from .models import ContactMessage


class ContactMessageForm(forms.ModelForm):
    """
    Form for contact messages with enhanced validation and styling
    """
    
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام و نام خانوادگی',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'آدرس ایمیل',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'شماره تماس (اختیاری)',
                'pattern': '[0-9+\-\(\)\s]+'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'موضوع پیام',
                'required': True
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'متن پیام شما...',
                'rows': 5,
                'required': True
            })
        }
        
        labels = {
            'name': 'نام و نام خانوادگی',
            'email': 'آدرس ایمیل',
            'phone': 'شماره تماس',
            'subject': 'موضوع',
            'message': 'پیام'
        }
        
        help_texts = {
            'phone': 'شماره تماس اختیاری است',
            'message': 'پیام خود را به تفصیل بنویسید'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes and RTL support
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'dir': 'rtl'
            })
            
            # Add required attribute for required fields
            if field.required:
                field.widget.attrs['required'] = True
    
    def clean_phone(self):
        """Validate phone number format"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove spaces and dashes
            phone = phone.replace(' ', '').replace('-', '')
            
            # Basic Iranian mobile/phone validation
            if not phone.replace('+', '').replace('(', '').replace(')', '').isdigit():
                raise forms.ValidationError('شماره تلفن معتبر نیست')
        
        return phone
    
    def clean_name(self):
        """Validate name field"""
        name = self.cleaned_data.get('name')
        if name:
            if len(name.strip()) < 2:
                raise forms.ValidationError('نام باید حداقل ۲ حرف باشد')
            
            # Check for valid characters (Persian, English, space)
            import re
            if not re.match(r'^[\u0600-\u06FFa-zA-Z\s]+$', name.strip()):
                raise forms.ValidationError('نام فقط باید شامل حروف فارسی یا انگلیسی باشد')
        
        return name.strip() if name else name
    
    def clean_subject(self):
        """Validate subject field"""
        subject = self.cleaned_data.get('subject')
        if subject:
            if len(subject.strip()) < 3:
                raise forms.ValidationError('موضوع باید حداقل ۳ حرف باشد')
        
        return subject.strip() if subject else subject
    
    def clean_message(self):
        """Validate message field"""
        message = self.cleaned_data.get('message')
        if message:
            if len(message.strip()) < 10:
                raise forms.ValidationError('پیام باید حداقل ۱۰ حرف باشد')
            
            if len(message.strip()) > 1000:
                raise forms.ValidationError('پیام نباید بیش از ۱۰۰۰ حرف باشد')
        
        return message.strip() if message else message 