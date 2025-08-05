from django.urls import path
from .views import TeacherDashboardView, TeacherCourseStudentView, TeacherCourseView, AllTeacherView, TeacherDetailView, TeacherCreateCourseView

app_name = 'teacher'

urlpatterns = [
    path('allteacher', AllTeacherView.as_view(), name='allteacher'),
    path('detail/<uuid:teacher_id>', TeacherDetailView.as_view(), name='detail'),
    path('dashboard', TeacherDashboardView.as_view(), name='teacherdashboard'),
    path('course', TeacherCourseView.as_view, name='teachercourse'),
    path('course/student', TeacherCourseStudentView.as_view, name='teachercourse'),
    path('create-course/', TeacherCreateCourseView.as_view(), name='teacher_create_course'),
]