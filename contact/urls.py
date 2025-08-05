from django.urls import path
from . import views

app_name = 'contact'

urlpatterns = [
    path('aboutus/', views.aboutus_view, name='aboutus'),
    path('contactus/', views.contactus_view, name='contactus'),
    path('ajax/contact/', views.ajax_contact_submit, name='ajax_contact'),
    path('api/contact-info/', views.get_contact_info_api, name='contact_info_api'),
]