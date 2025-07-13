from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy


class CustomLoginView(LoginView):
    template_name = ''
    redirect_authenticated_user = True

    pass


class CustomLogoutView(LogoutView):
    pass


# class CustomRegisterView():
#     pass
