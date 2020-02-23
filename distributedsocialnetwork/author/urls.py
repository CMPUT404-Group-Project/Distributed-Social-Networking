from django.conf.urls import url
from django.urls import path

from .views import index, createAuthorView, logoutView

urlpatterns = [
    path('', index, name="home"),
    path('register/', createAuthorView, name="register"),
    path('logout/', logoutView, name="logout"),
]