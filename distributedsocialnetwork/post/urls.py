from django.conf.urls import url
from django.urls import path

from .views import public_posts_list

urlpatterns = [
    path('', public_posts_list, name="public_posts_list"),

]
