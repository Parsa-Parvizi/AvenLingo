from django.urls import path
from .views import home_view, determination, advice, search_view, request_course, request_private_class
from account.views import TeacherApplicationView

app_name = 'core'

urlpatterns = [
    path('', home_view, name='home'),
    path('search/', search_view, name='search'),
    
    path('determination/', determination, name='determination'),
    path('advice/', advice, name='advice'),
    path('collaborate/', TeacherApplicationView.as_view(), name='collaborate'),
    path('request-course/', request_course, name='request-course'),
    path('request-private-class/', request_private_class, name='request-private-class'),
]