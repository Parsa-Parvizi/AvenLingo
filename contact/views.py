from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from .models import ContactUs, AboutUs, ContactMessage
from .forms import ContactMessageForm


def aboutus_view(request):
    """
    Display About Us page with dynamic content
    """
    # Get AboutUs content (only one record allowed)
    about = AboutUs.objects.first()
    
    # Fallback content if no AboutUs record exists
    if not about:
        about = {
            'title': 'درباره آکادمی زبان انگلیسی',
            'subtitle': 'آموزش با کیفیت، آینده‌ای روشن',
            'main_content': 'آکادمی زبان انگلیسی ما با هدف ارائه بهترین خدمات آموزشی تأسیس شده است.',
            'students_count': 1000,
            'teachers_count': 20,
            'courses_count': 50,
            'experience_years': 10,
        }
    
    context = {
        'about': about,
        'page_title': 'درباره ما',
    }
    
    return render(request, 'aboutus.html', context)


def contactus_view(request):
    """
    Display Contact Us page and handle contact form submission
    """
    # Get contact information
    contact_info = ContactUs.objects.first()
    
    # Initialize form
    form = ContactMessageForm()
    
    if request.method == 'POST':
        form = ContactMessageForm(request.POST)
        if form.is_valid():
            # Save contact message
            contact_message = form.save()
            
            # Send notification email to admin (optional)
            try:
                if hasattr(settings, 'EMAIL_HOST_USER') and settings.EMAIL_HOST_USER:
                    admin_email = getattr(settings, 'ADMIN_EMAIL', contact_info.email if contact_info else 'admin@academy.com')
                    
                    subject = f"پیام جدید از {contact_message.name}"
                    message = f"""
پیام جدید از سایت آکادمی دریافت شد:

نام: {contact_message.name}
ایمیل: {contact_message.email}
تلفن: {contact_message.phone}
موضوع: {contact_message.subject}

پیام:
{contact_message.message}

تاریخ ارسال: {contact_message.created_at.strftime('%Y/%m/%d %H:%M')}
                    """
                    
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[admin_email],
                        fail_silently=True
                    )
            except Exception:
                pass  # Don't break the flow if email fails
            
            messages.success(request, 'پیام شما با موفقیت ارسال شد. در اسرع وقت با شما تماس خواهیم گرفت.')
            return redirect('contact:contactus')
        else:
            messages.error(request, 'لطفاً اطلاعات را به درستی وارد کنید.')
    
    # Fallback contact info if none exists
    if not contact_info:
        contact_info = {
            'phone': '021-12345678',
            'mobile': '09123456789',
            'email': 'info@academy.com',
            'address': 'تهران، ایران',
            'instagram': 'https://instagram.com/academy',
            'telegram': 'https://t.me/academy',
            'whatsapp': '09123456789',
            'working_hours': 'شنبه تا پنج‌شنبه: ۸ صبح تا ۲۰',
        }
    
    context = {
        'contact_info': contact_info,
        'form': form,
        'page_title': 'تماس با ما',
    }
    
    return render(request, 'contactus.html', context)


@require_http_methods(["POST"])
def ajax_contact_submit(request):
    """
    Handle AJAX contact form submission
    """
    form = ContactMessageForm(request.POST)
    
    if form.is_valid():
        contact_message = form.save()
        
        # Send notification email
        try:
            contact_info = ContactUs.objects.first()
            admin_email = contact_info.email if contact_info else 'admin@academy.com'
            
            subject = f"پیام جدید از {contact_message.name}"
            message = f"نام: {contact_message.name}\nایمیل: {contact_message.email}\nموضوع: {contact_message.subject}\n\nپیام:\n{contact_message.message}"
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[admin_email],
                fail_silently=True
            )
        except Exception:
            pass
        
        return JsonResponse({
            'success': True,
            'message': 'پیام شما با موفقیت ارسال شد.'
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors,
            'message': 'لطفاً اطلاعات را به درستی وارد کنید.'
        })


def get_contact_info_api(request):
    """
    API endpoint to get contact information for JavaScript/AJAX calls
    """
    contact_info = ContactUs.objects.first()
    
    if contact_info:
        data = {
            'phone': contact_info.phone,
            'mobile': contact_info.mobile,
            'email': contact_info.email,
            'address': contact_info.address,
            'whatsapp_url': contact_info.whatsapp_url,
            'instagram': contact_info.instagram,
            'telegram': contact_info.telegram,
            'working_hours': contact_info.working_hours,
        }
    else:
        data = {
            'phone': '021-12345678',
            'mobile': '09123456789',
            'email': 'info@academy.com',
            'address': 'تهران، ایران',
            'whatsapp_url': 'https://wa.me/989123456789',
            'working_hours': 'شنبه تا پنج‌شنبه: ۸ صبح تا ۲۰',
        }
    
    return JsonResponse(data)
