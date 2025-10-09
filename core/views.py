from django.shortcuts import render, redirect
from django.db.models import Q, Prefetch, Count
from django.db import models
from django.core.cache import cache
from django.conf import settings
from django.contrib import messages
from course.models import Course
from account.models import Teacher
from course.models import Category
from .models import ContactMessage
from .forms import AdviceRequestForm, DeterminationRequestForm, RequestCourseForm, CollabrateRequestForm, ContactMessageForm, PrivateClassRequestForm
from account.forms import TeacherApplicationForm



def home_view(request):
    """صفحه اصلی با اسلایدرها"""
    
    # دوره‌های ویژه (حداکثر 9 تا از بهترین‌ها)
    featured_courses = Course.objects.filter(
        is_active=True, 
        is_featured=True,
        status='published'
    ).select_related('teacher', 'category').order_by('-created_at')[:9]
    
    # جدیدترین دوره‌ها (حداکثر 9 تا)
    latest_courses = Course.objects.filter(
        is_active=True,
        status='published'
    ).select_related('teacher', 'category').order_by('-created_at')[:9]
    
    # تمام دسته‌بندی‌های فعال
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    # تمام اساتید فعال و تأیید شده
    active_teachers = Teacher.objects.filter(
        is_active=True, 
        is_verified=True
    ).order_by('user__first_name')
    
    # Prepare context data
    context_data = {
        'page_title': "Home",
        'latest_courses': latest_courses,
        'featured_courses': featured_courses,
        'teachers': active_teachers,
        'categories': categories
    }
    
    return render(request, 'home.html', context_data)


def search_view(request):
    """Optimized search view with query optimization"""
    query = request.GET.get('q', '').strip()
    search_courses = request.GET.get('search_courses', False)
    search_teachers = request.GET.get('search_teachers', False)
    
    courses = []
    teachers = []
    
    if query and len(query) >= 2:  # Minimum query length
        if search_courses:
            # Optimized course search with select_related
            courses = Course.objects.select_related(
                'teacher', 'teacher__user', 'category'
            ).filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(teacher__full_name__icontains=query) |
                Q(category__name__icontains=query),
                is_active=True
            ).distinct().only(
                'id', 'title', 'description', 'price', 'level', 'slug',
                'teacher__full_name', 'category__name', 'image'
            )[:20]  # Limit results
        
        if search_teachers:
            # Optimized teacher search with select_related
            teachers = Teacher.objects.select_related('user').filter(
                Q(full_name__icontains=query) |
                Q(bio__icontains=query) |
                Q(expertise__icontains=query),
                is_active=True, is_verified=True
            ).distinct().only(
                'id', 'full_name', 'bio', 'expertise', 'image'
            )[:20]  # Limit results
    
    context = {
        'query': query,
        'courses': courses,
        'teachers': teachers,
        'search_courses': search_courses,
        'search_teachers': search_teachers,
        'total_results': len(courses) + len(teachers)
    }
    
    return render(request, 'search_results.html', context)


def determination(request):
    """صفحه درخواست تعیین سطح"""
    if request.method == 'POST':
        form = DeterminationRequestForm(request.POST)
        if form.is_valid():
            # ذخیره درخواست
            form.save()
            
            # نمایش پیام موفقیت
            messages.success(
                request,
                'درخواست تعیین سطح شما با موفقیت ثبت شد! کارشناسان ما در اسرع وقت با شما تماس خواهند گرفت.'
            )
            
            # Redirect برای جلوگیری از ارسال مجدد فرم
            return redirect('core:determination')
        else:
            # نمایش پیام خطا
            messages.error(
                request,
                'خطا در ثبت درخواست. لطفاً اطلاعات را بررسی کرده و دوباره تلاش کنید.'
            )
    else:
        form = DeterminationRequestForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'core/determination.html', context)


def advice(request):
    """صفحه درخواست مشاوره"""
    if request.method == 'POST':
        form = AdviceRequestForm(request.POST)
        if form.is_valid():
            # ذخیره درخواست
            form.save()
            
            # نمایش پیام موفقیت
            messages.success(
                request,
                'درخواست مشاوره شما با موفقیت ثبت شد! کارشناسان ما در اسرع وقت با شما تماس خواهند گرفت.'
            )
            
            # Redirect برای جلوگیری از ارسال مجدد فرم
            return redirect('core:advice')
        else:
            # نمایش پیام خطا
            messages.error(
                request,
                'خطا در ثبت درخواست. لطفاً اطلاعات را بررسی کرده و دوباره تلاش کنید.'
            )
    else:
        form = AdviceRequestForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'core/advice.html', context)




def request_course(request):
    """صفحه درخواست دوره جدید"""
    if request.method == 'POST':
        form = RequestCourseForm(request.POST)
        if form.is_valid():
            # ذخیره درخواست
            form.save()
            
            # نمایش پیام موفقیت
            messages.success(
                request,
                'درخواست دوره شما با موفقیت ثبت شد! ما به زودی دوره مورد نظر شما را بررسی می‌کنیم.'
            )
            
            # Redirect برای جلوگیری از ارسال مجدد فرم
            return redirect('core:request-course')
        else:
            # نمایش پیام خطا
            messages.error(
                request,
                'خطا در ثبت درخواست. لطفاً اطلاعات را بررسی کرده و دوباره تلاش کنید.'
            )
    else:
        form = RequestCourseForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'request_course.html', context)


def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)


def custom_500(request):
    return render(request, 'errors/500.html', status=500)


def custom_403(request, exception):
    return render(request, 'errors/403.html', status=403)


def custom_400(request, exception):
    return render(request, 'errors/400.html', status=400)



def aboutus_view(request):
    return render(request, 'contact/aboutus.html')


def contactus_view(request):
    """صفحه تماس با ما با فرم ارسال پیام"""
    from datetime import date, timedelta
    from django.utils import timezone
    
    # بررسی محدودیت روزانه
    can_submit = True
    remaining_attempts = 3
    
    if request.method == 'POST':
        # بررسی تعداد پیام‌های ارسال شده امروز
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # بررسی بر اساس IP
        user_ip = request.META.get('REMOTE_ADDR')
        today_messages_count = ContactMessage.objects.filter(
            created_at__gte=today_start
        ).filter(
            models.Q(email=request.POST.get('email')) |
            models.Q(phone=request.POST.get('phone'))
        ).count()
        
        if today_messages_count >= 3:
            can_submit = False
            messages.error(
                request,
                'شما امروز 3 پیام ارسال کرده‌اید. لطفاً فردا دوباره تلاش کنید.'
            )
        else:
            form = ContactMessageForm(request.POST)
            if form.is_valid():
                # ذخیره پیام
                contact_message = form.save()
                
                # نمایش پیام موفقیت
                remaining = 3 - today_messages_count - 1
                messages.success(
                    request,
                    f'پیام شما با موفقیت ارسال شد! در اسرع وقت با شما تماس خواهیم گرفت. (امروز {remaining} پیام دیگر می‌توانید ارسال کنید)'
                )
                
                # Redirect برای جلوگیری از ارسال مجدد فرم
                return redirect('contactus')
            else:
                # نمایش پیام خطا
                messages.error(
                    request,
                    'خطا در ارسال پیام. لطفاً اطلاعات را بررسی کرده و دوباره تلاش کنید.'
                )
    else:
        form = ContactMessageForm()
        
        # محاسبه پیام‌های باقی‌مانده برای نمایش
        if request.user.is_authenticated:
            today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_messages_count = ContactMessage.objects.filter(
                email=request.user.email,
                created_at__gte=today_start
            ).count()
            remaining_attempts = max(0, 3 - today_messages_count)
    
    context = {
        'form': form,
        'remaining_attempts': remaining_attempts,
    }
    
    return render(request, 'contact/contactus.html', context)


def request_private_class(request):
    """صفحه درخواست کلاس خصوصی"""
    if request.method == 'POST':
        form = PrivateClassRequestForm(request.POST)
        if form.is_valid():
            # ذخیره درخواست
            private_class_request = form.save()
            
            # نمایش پیام موفقیت
            messages.success(
                request,
                'درخواست کلاس خصوصی شما با موفقیت ثبت شد! کارشناسان ما در اسرع وقت با شما تماس خواهند گرفت.'
            )
            
            # Redirect برای جلوگیری از ارسال مجدد فرم
            return redirect('core:request-private-class')
        else:
            # نمایش پیام خطا
            messages.error(
                request,
                'خطا در ثبت درخواست. لطفاً اطلاعات را بررسی کرده و دوباره تلاش کنید.'
            )
    else:
        form = PrivateClassRequestForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'core/request_private_class.html', context)

