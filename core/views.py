from django.shortcuts import render
from django.db.models import Q
from course.models import Course
from teacher.models import Teacher
from .models import FAQ, CourseGuide
from course.models import Category
from django.shortcuts import render, redirect
from .forms import AdviceRequestForm, DeterminationRequestForm, CollabrateRequestForm, RequestCourseForm


def home_view(request):
    active_courses = Course.objects.filter(is_active=True)  # type: ignore
    latest_courses = Course.objects.filter(is_active=True).order_by('-created_at')[:4]  # type: ignore
    featured_courses = Course.objects.filter(is_active=True, is_featured=True)[:3]  # type: ignore
    active_teachers = Teacher.objects.filter(is_active=True)  # type: ignore
    faqs = FAQ.objects.filter(is_active=True)  # type: ignore
    course_guide = CourseGuide.objects.filter(is_active=True).first()  # type: ignore
    categories = Category.objects.filter(is_active=True)[:6]  # type: ignore

    return render(request, 'home.html', {
        'page_title': "Home",
        'courses': active_courses,
        'latest_courses': latest_courses,
        'featured_courses': featured_courses,
        'teachers': active_teachers,
        'faqs': faqs,
        'course_guide': course_guide,
        'categories': categories
    })


def search_view(request):
    query = request.GET.get('q', '')
    search_courses = request.GET.get('search_courses', False)
    search_teachers = request.GET.get('search_teachers', False)
    
    courses = []
    teachers = []
    
    if query:
        if search_courses:
            courses = Course.objects.filter( # type: ignore
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(short_description__icontains=query) | # type: ignore
                Q(teacher__full_name__icontains=query) |
                Q(category__name__icontains=query),
                is_active=True
            ).distinct()
        
        if search_teachers:
            teachers = Teacher.objects.filter( # type: ignore
                Q(full_name__icontains=query) |
                Q(bio__icontains=query) |
                Q(specialization__icontains=query), # type: ignore
                is_active=True
            ).distinct()
    
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
    # درخواست
    if request.method == 'POST':
        form = CollabrateRequestForm(request.POST)
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
