from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard_home'),
    path('student/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    path('teacher/', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),
    
    # Admin Dashboard URLs - Redirect to Calendar
    path('admin/', lambda request: redirect('dashboard:admin_calendar'), name='admin_dashboard'),
    path('admin/users/', views.AdminUsersListView.as_view(), name='admin_users'),
    path('admin/users/<uuid:user_id>/', views.AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('admin/courses/', views.AdminCoursesListView.as_view(), name='admin_courses'),
    path('admin/courses/<int:course_id>/', views.AdminCourseDetailView.as_view(), name='admin_course_detail'),
    path('admin/enrollments/', views.AdminEnrollmentsListView.as_view(), name='admin_enrollments'),
    path('admin/enrollments/<int:enrollment_id>/', views.AdminEnrollmentDetailView.as_view(), name='admin_enrollment_detail'),
    path('admin/enrollments/<int:enrollment_id>/approve/', views.admin_approve_enrollment, name='admin_approve_enrollment'),
    path('admin/enrollments/<int:enrollment_id>/reject/', views.admin_reject_enrollment, name='admin_reject_enrollment'),
    
    # Financial Management
    path('admin/financial/', views.AdminFinancialView.as_view(), name='admin_financial'),
    path('admin/financial/export-pdf/', views.export_financial_pdf, name='export_financial_pdf'),
    
    # Requests Management
    path('admin/applications/', views.AdminApplicationsListView.as_view(), name='admin_applications'),
    path('admin/applications/<uuid:application_id>/', views.AdminApplicationDetailView.as_view(), name='admin_application_detail'),
    path('admin/applications/<uuid:application_id>/approve/', views.admin_approve_application, name='admin_approve_application'),
    path('admin/applications/<uuid:application_id>/reject/', views.admin_reject_application, name='admin_reject_application'),
    path('admin/course-requests/', views.AdminCourseRequestsView.as_view(), name='admin_course_requests'),
    path('admin/consultation-requests/', views.AdminConsultationRequestsView.as_view(), name='admin_consultation_requests'),
    path('admin/level-assessment-requests/', views.AdminLevelAssessmentRequestsView.as_view(), name='admin_level_assessment_requests'),
    path('admin/level-assessment-requests/<int:request_id>/', views.AdminLevelAssessmentDetailView.as_view(), name='admin_level_assessment_detail'),
    path('admin/private-class-requests/', views.AdminPrivateClassRequestsView.as_view(), name='admin_private_class_requests'),
    path('admin/private-class-requests/<int:request_id>/', views.AdminPrivateClassRequestDetailView.as_view(), name='admin_private_class_request_detail'),
    path('admin/contact-messages/', views.AdminContactMessagesView.as_view(), name='admin_contact_messages'),
    path('admin/contact-messages/<int:message_id>/', views.AdminContactMessageDetailView.as_view(), name='admin_contact_message_detail'),
    
    # Calendar
    path('admin/calendar/', views.AdminCalendarView.as_view(), name='admin_calendar'),
    path('student/calendar/', views.StudentCalendarView.as_view(), name='student_calendar'),
    
    # Security & Settings
    path('admin/login-history/', views.AdminLoginHistoryView.as_view(), name='admin_login_history'),
    path('admin/sessions/', views.AdminSessionsView.as_view(), name='admin_sessions'),
    path('admin/permissions/', views.AdminPermissionsView.as_view(), name='admin_permissions'),
    path('admin/security-settings/', views.AdminSecuritySettingsView.as_view(), name='admin_security_settings'),
    
    # Admin Actions
    path('admin/teacher/register/', views.AdminTeacherRegisterView.as_view(), name='admin_teacher_register'),
    path('admin/student/register/', views.AdminStudentRegisterView.as_view(), name='admin_student_register'),
    path('admin/session/<str:session_key>/delete/', views.delete_session, name='delete_session'),
] 