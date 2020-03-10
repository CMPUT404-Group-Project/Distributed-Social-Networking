from django.urls import path
from .views import create


urlpatterns = [
    path('create', create, name='create')
]
