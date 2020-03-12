from django.urls import path
from .views import create_post, view_post

app_name= 'post'
urlpatterns = [
    path('create', create_post, name='create'),
    path('<uuid:pk>', view_post, name='view_post')
]
