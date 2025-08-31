from django.urls import path
from . import views

app_name = 'enrollment'

urlpatterns = [
    # Student enrollment management
    path('my-enrollments/', views.StudentEnrollmentListView.as_view(), name='my-enrollments'),
    path('enrollment/<int:pk>/', views.EnrollmentDetailView.as_view(), name='enrollment-detail'),
    
    # Course enrollment
    path('enroll/<int:course_id>/', views.CourseEnrollmentView.as_view(), name='enroll'),
    path('quick-enroll/', views.QuickEnrollView.as_view(), name='quick-enroll'),
    
    # Enrollment management
    path('cancel/<int:enrollment_id>/', views.cancel_enrollment, name='cancel-enrollment'),
    path('certificate/<int:enrollment_id>/', views.enrollment_certificate, name='certificate'),
    
    # Course browsing
    path('available-courses/', views.AvailableCoursesView.as_view(), name='available-courses'),
]
