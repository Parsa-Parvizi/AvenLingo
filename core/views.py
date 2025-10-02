from django.shortcuts import render, redirect
from django.db.models import Q, Prefetch, Count
from django.core.cache import cache
from django.conf import settings
from course.models import Course
from account.models import Teacher
from course.models import Category
from .forms import AdviceRequestForm, DeterminationRequestForm, RequestCourseForm, CollabrateRequestForm
from account.forms import TeacherApplicationForm



def home_view(request):
    """Basic home view for development"""
    
    # Basic queries for development
    courses_queryset = Course.objects.filter(is_active=True).order_by('-created_at')
    
    # Get courses
    latest_courses = courses_queryset[:4]
    featured_courses = courses_queryset.filter(is_featured=True)[:3]
    
    # Basic teacher query
    active_teachers = Teacher.objects.filter(
        is_active=True, is_verified=True
    )[:10]
    
    # Basic categories query
    categories = Category.objects.filter(is_active=True).order_by('name')[:6]
    
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
    # درخواست تعیین سطح
    if request.method == 'POST':
        form = DeterminationRequestForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'core/application_success.html', {'message': 'درخواست تعیین سطح با موفقیت ثبت شد.'})
    else:
        form = DeterminationRequestForm()
    return render(request, 'core/determination.html', {'form': form})


def advice(request):
    # درخواست مشاوره
    if request.method == 'POST':
        form = AdviceRequestForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'core/application_success.html', {'message': 'درخواست مشاوره با موفقیت ثبت شد.'})
    else:
        form = AdviceRequestForm()
        
    return render(request, 'core/advice.html', {'form': form})


def collabrate(request):
    # درخواست همکاری
    if request.method == 'POST':
        form = CollabrateRequestForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return render(request, 'core/application_success.html', {'message': 'درخواست همکاری با موفقیت ثبت شد.'})
    else:
        form = CollabrateRequestForm()
    return render(request, 'core/collabrate.html', {'form': form})


def request_course(request):
    if request.method == 'POST':
        form = RequestCourseForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'request_course_success.html', {'message': 'درخواست شما با موفقیت ثبت شد.'})
    else:
        form = RequestCourseForm()
    return render(request, 'request_course.html', {'form': form})


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
    
    return render(request, 'contact/contactus.html')

