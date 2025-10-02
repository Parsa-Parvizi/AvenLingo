from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard_home'),
    path('student/<uuid:student_id>/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    path('teacher/', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),
    
    # Admin Dashboard URLs
    path('admin/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/users/', views.AdminUsersListView.as_view(), name='admin_users'),
    path('admin/courses/', views.AdminCoursesListView.as_view(), name='admin_courses'),
    path('admin/enrollments/', views.AdminEnrollmentsListView.as_view(), name='admin_enrollments'),
    
    # Requests Management
    path('admin/applications/', views.AdminApplicationsListView.as_view(), name='admin_applications'),
    path('admin/course-requests/', views.AdminCourseRequestsView.as_view(), name='admin_course_requests'),
    path('admin/consultation-requests/', views.AdminConsultationRequestsView.as_view(), name='admin_consultation_requests'),
    
    # Security & Settings
    path('admin/login-history/', views.AdminLoginHistoryView.as_view(), name='admin_login_history'),
    path('admin/sessions/', views.AdminSessionsView.as_view(), name='admin_sessions'),
    path('admin/permissions/', views.AdminPermissionsView.as_view(), name='admin_permissions'),
    path('admin/security-settings/', views.AdminSecuritySettingsView.as_view(), name='admin_security_settings'),
    
    # Admin Actions
    path('admin/teacher/register/', views.AdminTeacherRegisterView.as_view(), name='admin_teacher_register'),
    path('admin/session/<int:pk>/delete/', views.delete_session, name='delete_session'),
] 