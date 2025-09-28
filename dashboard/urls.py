from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard_home'),
    path('student/<uuid:student_id>/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    path('teacher/', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),
] 