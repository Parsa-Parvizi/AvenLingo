from django.urls import path
from . import views

app_name = 'enrollment'

urlpatterns = [
    # Student enrollment management
    path('my-enrollments/', views.StudentEnrollmentListView.as_view(), name='student_enrollments'),
    path('enrollment/<int:pk>/', views.EnrollmentDetailView.as_view(), name='enrollment_detail'),
    
    # Course enrollment
    path('enroll/<int:course_id>/', views.CourseEnrollmentView.as_view(), name='course_enroll'),
    path('quick-enroll/', views.QuickEnrollView.as_view(), name='quick_enroll'),
    
    # Enrollment management
    path('cancel/<int:enrollment_id>/', views.cancel_enrollment, name='cancel_enrollment'),
    path('certificate/<int:enrollment_id>/', views.enrollment_certificate, name='enrollment_certificate'),
    
    # Course browsing
    path('courses/', views.AvailableCoursesView.as_view(), name='available_courses'),
]
