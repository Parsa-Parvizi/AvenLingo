from django.urls import path
from .views import TeacherDashboardView, TeacherCourseStudentView, TeacherCourseView, AllTeacherView, TeacherDetailView, TeacherCreateCourseView, TeacherScheduleView, TeacherPerformanceView, TeacherMessagesView
app_name = 'teacher'

urlpatterns = [
    path('all-teachers/', AllTeacherView.as_view(), name='all-teachers'),
    path('detail/<int:teacher_id>/', TeacherDetailView.as_view(), name='detail'),
    path('dashboard/', TeacherDashboardView.as_view(), name='dashboard'),
    path('courses/', TeacherCourseView.as_view(), name='courses'),
    path('courses/<int:course_id>/students/', TeacherCourseStudentView.as_view(), name='course-students'),
    path('create-course/', TeacherCreateCourseView.as_view(), name='create-course'),
    path('schedule/', TeacherScheduleView.as_view(), name='schedule'), # Placeholder
    path('performance/', TeacherPerformanceView.as_view(), name='performance'), # Placeholder
    path('messages/', TeacherMessagesView.as_view(), name='messages'), # Placeholder
]