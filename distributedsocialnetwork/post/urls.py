from django.urls import path
from .views import create_post, view_post, edit_post, delete_post

app_name = 'post'
urlpatterns = [
    path('create', create_post, name='create'),
    path('<uuid:pk>', view_post, name='view_post'),
    path('<uuid:pk>/edit', edit_post, name='edit_post'),
    path('<uuid:pk>/delete', delete_post, name='delete_post')
]
