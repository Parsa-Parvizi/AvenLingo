from django.urls import path
from .views import (
    TeacherDashboardView, TeacherCourseStudentView, TeacherCourseView, AllTeacherView, 
    TeacherDetailView, TeacherCreateCourseView, TeacherEditCourseView, TeacherScheduleView, 
    TeacherPerformanceView, TeacherMessagesView, TeacherAssignmentsView, TeacherCreateAssignmentView,
    TeacherEditAssignmentView, TeacherDeleteAssignmentView, TeacherAssignmentDetailView,
    TeacherActivitiesView, TeacherNotificationsView, TeacherMyStudentsView,
    TeacherExamsListView, TeacherExamsView, TeacherCreateExamView, TeacherEditExamView, TeacherDeleteExamView,
    TeacherExamParticipantsView, TeacherGradeExamView
)
app_name = 'teacher'

urlpatterns = [
    path('all-teachers/', AllTeacherView.as_view(), name='all-teachers'),
    path('detail/<int:teacher_id>/', TeacherDetailView.as_view(), name='detail'),
    path('dashboard/', TeacherDashboardView.as_view(), name='dashboard'),
    path('courses/', TeacherCourseView.as_view(), name='teacher_courses'),
    path('my-students/', TeacherMyStudentsView.as_view(), name='my_students'),
    path('courses/<int:course_id>/students/', TeacherCourseStudentView.as_view(), name='course-students'),
    path('create-course/', TeacherCreateCourseView.as_view(), name='create-course'),
    path('edit-course/<int:course_id>/', TeacherEditCourseView.as_view(), name='edit-course'),
    
    # Assignment URLs
    path('assignments/', TeacherAssignmentsView.as_view(), name='assignments'),
    path('courses/<int:course_id>/assignments/', TeacherAssignmentsView.as_view(), name='course_assignments'),
    path('courses/<int:course_id>/assignments/create/', TeacherCreateAssignmentView.as_view(), name='create_assignment'),
    path('assignments/<int:assignment_id>/', TeacherAssignmentDetailView.as_view(), name='assignment_detail'),
    path('assignments/<int:assignment_id>/edit/', TeacherEditAssignmentView.as_view(), name='edit_assignment'),
    path('assignments/<int:assignment_id>/delete/', TeacherDeleteAssignmentView.as_view(), name='delete_assignment'),
    
    # Exam URLs
    path('exams/', TeacherExamsListView.as_view(), name='exams_list'),
    path('courses/<int:course_id>/exams/', TeacherExamsView.as_view(), name='course_exams'),
    path('courses/<int:course_id>/exams/create/', TeacherCreateExamView.as_view(), name='create_exam'),
    path('exams/<int:exam_id>/edit/', TeacherEditExamView.as_view(), name='edit_exam'),
    path('exams/<int:exam_id>/delete/', TeacherDeleteExamView.as_view(), name='delete_exam'),
    path('exams/<int:exam_id>/participants/', TeacherExamParticipantsView.as_view(), name='exam_participants'),
    path('exams/<int:exam_id>/grade/<int:participation_id>/', TeacherGradeExamView.as_view(), name='grade_exam'),
    
    # Additional URLs
    path('activities/', TeacherActivitiesView.as_view(), name='activities'),
    path('notifications/', TeacherNotificationsView.as_view(), name='notifications'),
    
    path('calendar/', TeacherScheduleView.as_view(), name='calendar'), # Integrated with schedule
    path('schedule/', TeacherScheduleView.as_view(), name='schedule'), # Alias for calendar
    path('performance/', TeacherPerformanceView.as_view(), name='performance'), # Placeholder
    path('messages/', TeacherMessagesView.as_view(), name='messages'), # Placeholder
]