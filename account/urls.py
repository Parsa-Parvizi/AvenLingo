from django.urls import path
from . import views
from dashboard import views as dashboard_views

app_name = 'account'

urlpatterns = [
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # Password Reset URLs
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Email Verification URLs
    path('email-verification/', views.EmailVerificationView.as_view(), name='email_verification'),
    path('verify-email/<int:user_id>/<str:token>/', views.verify_email, name='verify_email'),
    
    # Registration URLs
    path('register/student/', views.StudentRegistrationView.as_view(), name='student_register'),
    path('register/teacher/<str:email>/', views.TeacherRegistrationView.as_view(), name='teacher_register'),
    path('check-teacher-registration/<str:email>/', views.check_teacher_registration, name='check_teacher_registration'),
    
    # AJAX URLs
    path('validate-email/', views.validate_email, name='validate_email'),
    
    # Dashboard URL
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Profile URLs
    path('profile/student/', views.StudentProfileView.as_view(), name='student_profile'),
    path('profile/teacher/', views.TeacherProfileView.as_view(), name='teacher_profile'),
    
    # Teacher Application URLs
    path('teacher/apply/success/', views.TeacherApplicationSuccessView.as_view(), name='teacher_apply_success'),
    
    # Admin URLs for Teacher Applications
    path('admin/teacher-applications/', views.TeacherApplicationListView.as_view(), name='admin_teacher_applications'),
    path('admin/teacher-applications/<uuid:pk>/', views.TeacherApplicationDetailView.as_view(), name='admin_teacher_application_detail'),
    path('admin/teacher-applications/<uuid:pk>/approve/', views.TeacherApplicationApprovalView.as_view(), name='admin_teacher_application_approve'),
]
