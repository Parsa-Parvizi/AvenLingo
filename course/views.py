from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
from .models import Course, Category, LANGUAGE_CHOICES

def all_courses_view(request):
    """نمایش همه کلاس‌ها با فیلتر"""
    courses = Course.objects.filter(is_active=True)  # type: ignore
    

    
    # فیلتر بر اساس سطح
    level = request.GET.get('level')
    if level:
        courses = courses.filter(level=level)
    
    # فیلتر بر اساس گروه سنی
    age_group = request.GET.get('age_group')
    if age_group:
        courses = courses.filter(age_group=age_group)
    
    # فیلتر بر اساس نوع (آنلاین/حضوری)
    course_type = request.GET.get('type')
    if course_type == 'online':
        courses = courses.filter(is_online=True)
    elif course_type == 'offline':
        courses = courses.filter(is_online=False)
    
    # فیلتر بر اساس زبان
    language = request.GET.get('language')
    if language:
        courses = courses.filter(category__language=language)
    
    # فیلتر بر اساس نوع کلاس
    class_type = request.GET.get('class_type')
    if class_type:
        courses = courses.filter(class_type=class_type)
    
    # جستجو
    search = request.GET.get('search')
    if search:
        courses = courses.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(teacher__full_name__icontains=search) # type: ignore
        )
    
    categories = Category.objects.filter(is_active=True)  # type: ignore
    
    context = {
        'courses': courses,
        'categories': categories,
        'current_level': level,
        'current_age_group': age_group,
        'current_type': course_type,
        'current_language': language,
        'current_class_type': class_type,
        'search': search,
        'languages': dict(LANGUAGE_CHOICES),
        'class_types': dict(Course.CLASS_TYPE_CHOICES),
    }
    
    return render(request, 'course/all_courses.html', context)


def featured_courses_view(request):
    """نمایش کلاس‌های ویژه"""
    featured_courses = Course.objects.filter(is_active=True, is_featured=True)  # type: ignore
    return render(request, 'course/featured_courses.html', {'courses': featured_courses})


def category_courses_view(request, category_slug):
    """نمایش کلاس‌های یک دسته‌بندی خاص"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    courses = Course.objects.filter(category=category, is_active=True)  # type: ignore
    
    context = {
        'category': category,
        'courses': courses,
    }
    
    return render(request, 'course/category_courses.html', context)


def course_detail_view(request, course_slug):
    """نمایش جزئیات کلاس"""
    course = get_object_or_404(Course, slug=course_slug, is_active=True)
    
    # کلاس‌های مشابه
    similar_courses = Course.objects.filter( # type: ignore
        is_active=True,
        category=course.category
    ).exclude(id=course.id)[:3]  # type: ignore
    
    context = {
        'course': course,
        'similar_courses': similar_courses,
    }
    
    return render(request, 'course/course_detail.html', context)


def latest_courses_view(request):
    """نمایش آخرین کلاس‌ها"""
    latest_courses = Course.objects.filter(is_active=True).order_by('-created_at')[:6]  # type: ignore
    return render(request, 'course/latest_courses.html', {'courses': latest_courses})


