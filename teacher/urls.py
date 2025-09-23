from django.urls import path
from .views import TeacherDashboardView, TeacherCourseStudentView, TeacherCourseView, AllTeacherView, TeacherDetailView, TeacherCreateCourseView

app_name = 'teacher'

urlpatterns = [
    path('all-teachers/', AllTeacherView.as_view(), name='all-teachers'),
    path('detail/<uuid:teacher_id>/', TeacherDetailView.as_view(), name='detail'),
    path('dashboard/', TeacherDashboardView.as_view(), name='dashboard'),
    path('courses/', TeacherCourseView.as_view(), name='courses'),
    path('courses/<int:course_id>/students/', TeacherCourseStudentView.as_view(), name='course-students'),
    path('create-course/', TeacherCreateCourseView.as_view(), name='create-course'),
]