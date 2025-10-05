from django.urls import path
from .views import (
    all_courses_view, 
    featured_courses_view, 
    category_courses_view, 
    course_detail_view, 
    latest_courses_view,
    student_course_detail_view,
    AssignmentCreateView,
    AssignmentListView,
    AssignmentDetailView,
    AssignmentSubmissionView,
    AssignmentSubmissionGradingView,
    download_assignment_file,
    download_submission_file
)

app_name = 'course'

urlpatterns = [
    path('', all_courses_view, name='all-courses'),
    path('featured/', featured_courses_view, name='featured'),
    path('latest/', latest_courses_view, name='latest'),
    path('category/<str:category_slug>/', category_courses_view, name='category'),
    path('detail/<str:course_slug>/', course_detail_view, name='detail'),
    path('student-course/<int:course_id>/', student_course_detail_view, name='student-course-detail'),
    
    # Assignment URLs
    path('course/<int:course_id>/assignments/', AssignmentListView.as_view(), name='assignment_list'),
    path('course/<int:course_id>/assignment/create/', AssignmentCreateView.as_view(), name='assignment_create'),
    path('assignment/<int:pk>/', AssignmentDetailView.as_view(), name='assignment_detail'),
    path('assignment/<int:assignment_id>/submit/', AssignmentSubmissionView.as_view(), name='assignment_submit'),
    path('submission/<int:pk>/grade/', AssignmentSubmissionGradingView.as_view(), name='assignment_grade'),
    
    # File Download URLs
    path('assignment/<int:assignment_id>/download/', download_assignment_file, name='assignment_download'),
    path('submission/<int:submission_id>/download/', download_submission_file, name='submission_download'),
]