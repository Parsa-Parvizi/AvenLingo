from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Registration URLs
    path('register/student/', views.StudentRegistrationView.as_view(), name='student_register'),
    path('register/teacher/<str:email>/', views.TeacherRegistrationView.as_view(), name='teacher_register'),
    path('check-teacher-registration/<str:email>/', views.check_teacher_registration, name='check_teacher_registration'),
    
    # Dashboard URLs
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/student/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    path('dashboard/teacher/', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),
    
    # Profile URLs
    path('profile/student/', views.StudentProfileView.as_view(), name='student_profile'),
    path('profile/teacher/', views.TeacherProfileView.as_view(), name='teacher_profile'),
    
    # Teacher Application URLs
    path('teacher/apply/', views.TeacherApplicationView.as_view(), name='teacher_apply'),
    path('teacher/apply/success/', views.TeacherApplicationSuccessView.as_view(), name='teacher_apply_success'),
    
    # Admin URLs for Teacher Applications
    path('admin/teacher-applications/', views.TeacherApplicationListView.as_view(), name='admin_teacher_applications'),
    path('admin/teacher-applications/<uuid:pk>/', views.TeacherApplicationDetailView.as_view(), name='admin_teacher_application_detail'),
    path('admin/teacher-applications/<uuid:pk>/approve/', views.TeacherApplicationApprovalView.as_view(), name='admin_teacher_application_approve'),
]
