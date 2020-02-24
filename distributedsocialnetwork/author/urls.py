from django.conf.urls import url
from django.urls import path

from .views import index, createAuthorView, loginView, logoutView

urlpatterns = [
    path('', index, name="home"),
    path('register/', createAuthorView, name="register"),
    path('login/', loginView, name="login"),
    path('logout/', logoutView, name="logout"),
]