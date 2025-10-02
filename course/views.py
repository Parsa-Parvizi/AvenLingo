from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Case, When, IntegerField, Count
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from .models import Course, Category, LANGUAGE_CHOICES, CLASS_TYPE_CHOICES, ONLINE_CHOICES
import re


def all_courses_view(request):
    """نمایش همه کلاس‌ها با جستجو و فیلتر پیشرفته"""
    # شروع با دوره‌های فعال
    courses = Course.objects.select_related('teacher', 'category').filter(is_active=True)
    
    # متغیرهای فیلتر
    level = request.GET.get('level', '').strip()
    age_group = request.GET.get('age_group', '').strip()
    course_type = request.GET.get('type', '').strip()
    language = request.GET.get('language', '').strip()
    class_type = request.GET.get('class_type', '').strip()
    search = request.GET.get('search', '').strip()
    
    # جستجوی پیشرفته و هوشمند
    if search:
        # تقسیم کلمات جستجو
        search_terms = re.findall(r'\w+', search.lower())
        
        if search_terms:
            # ایجاد کوئری پیچیده برای جستجوی هوشمند
            search_queries = Q()
            
            for term in search_terms:
                # جستجو در فیلدهای مختلف با وزن‌های متفاوت
                term_query = (
                    # عنوان دوره (وزن بالا)
                    Q(title__icontains=term) |
                    
                    # نام کامل معلم (وزن بالا)
                    Q(teacher__user__first_name__icontains=term) |
                    Q(teacher__user__last_name__icontains=term) |
                    
                    # توضیحات کوتاه (وزن متوسط)
                    Q(short_description__icontains=term) |
                    
                    # توضیحات کامل (وزن پایین)
                    Q(description__icontains=term) |
                    
                    # دسته‌بندی (وزن متوسط)
                    Q(category__name__icontains=term) |
                    
                    # نوع کلاس (وزن متوسط)
                    Q(class_type__icontains=term) |
                    
                    # سطح (وزن متوسط)
                    Q(level__icontains=term) |
                    
                    # گروه سنی (وزن متوسط)
                    Q(age_group__icontains=term) |
                    
                    # محل برگزاری (وزن پایین)
                    Q(location__icontains=term)
                )
                
                search_queries &= term_query
            
            courses = courses.filter(search_queries)
            
            # اولویت‌بندی نتایج بر اساس میزان تطبیق
            courses = courses.annotate(
                relevance_score=Case(
                    # تطبیق کامل عنوان
                    When(title__iexact=search, then=100),
                    # شروع عنوان با عبارت جستجو
                    When(title__istartswith=search, then=90),
                    # حاوی عبارت جستجو در عنوان
                    When(title__icontains=search, then=80),
                    
                    # تطبیق کامل نام معلم
                    When(Q(teacher__user__first_name__iexact=search) | 
                         Q(teacher__user__last_name__iexact=search), then=85),
                    # شروع نام معلم با عبارت جستجو
                    When(Q(teacher__user__first_name__istartswith=search) | 
                         Q(teacher__user__last_name__istartswith=search), then=75),
                    # حاوی عبارت جستجو در نام معلم
                    When(Q(teacher__user__first_name__icontains=search) | 
                         Q(teacher__user__last_name__icontains=search), then=70),
                    
                    # تطبیق در توضیحات کوتاه
                    When(short_description__icontains=search, then=60),
                    # تطبیق در دسته‌بندی
                    When(category__name__icontains=search, then=55),
                    # تطبیق در نوع کلاس
                    When(class_type__icontains=search, then=50),
                    # تطبیق در سایر فیلدها
                    default=30,
                    output_field=IntegerField()
                )
            ).order_by('-relevance_score', '-is_featured', '-created_at')
    else:
        # ترتیب پیش‌فرض بدون جستجو
        courses = courses.order_by('-is_featured', '-created_at')
    
    # اعمال فیلترها
    if level:
        courses = courses.filter(level=level)
    
    if age_group:
        courses = courses.filter(age_group=age_group)
    
    if course_type:
        if course_type == 'online':
            courses = courses.filter(is_online=True)
        elif course_type == 'offline':
            courses = courses.filter(is_online=False)
        elif course_type == 'in_person':
            courses = courses.filter(is_online=False, location__isnull=False)
    
    if language:
        courses = courses.filter(category__language=language)
    
    if class_type:
        courses = courses.filter(class_type=class_type)
    
    # دریافت دسته‌بندی‌ها برای فیلتر
    categories = Category.objects.filter(is_active=True)
    
    # محاسبه آمار جستجو
    total_courses = Course.objects.filter(is_active=True).count()
    filtered_count = courses.count()
    
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
        'class_types': dict(CLASS_TYPE_CHOICES),
        'online_choices': dict(ONLINE_CHOICES),
        'total_courses': total_courses,
        'filtered_count': filtered_count,
        'has_filters': any([level, age_group, course_type, language, class_type, search]),
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


