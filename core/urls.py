from django.urls import path
from .views import home_view, determination, advice, search_view, collabrate, request_course

app_name = 'core'

urlpatterns = [
    path('', home_view, name='home'),
    path('search/', search_view, name='search'),
    
    path('determination/', determination, name='determination'),
    path('advice/', advice, name='advice'),
    path('collaborate/', collabrate, name='collaborate'),
    path('request-course/', request_course, name='request-course'),
]