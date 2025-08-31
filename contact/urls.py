from django.urls import path
from . import views

app_name = 'contact'

urlpatterns = [
    path('about-us/', views.aboutus_view, name='about-us'),
    path('contactus/', views.contactus_view, name='contact-us'),
    path('ajax/contact/', views.ajax_contact_submit, name='ajax-contact'),
    path('api/contact-info/', views.get_contact_info_api, name='contact-info-api'),
]