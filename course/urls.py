from django.urls import path
from .views import (
    all_courses_view, 
    featured_courses_view, 
    category_courses_view, 
    course_detail_view, 
    latest_courses_view
)

app_name = 'course'

urlpatterns = [
    path('', all_courses_view, name='all-courses'),
    path('featured/', featured_courses_view, name='featured'),
    path('latest/', latest_courses_view, name='latest'),
    path('category/<slug:category_slug>/', category_courses_view, name='category'),
    path('detail/<slug:course_slug>/', course_detail_view, name='detail'),
]