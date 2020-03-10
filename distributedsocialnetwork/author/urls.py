from django.urls import path

from .views import (
    index,
    create_author,
    change_author,
    login_author,
    logout_author,
    view_author
)

urlpatterns = [
    path('', index,),
    path('register/', create_author, name="register"),
    path('update/', change_author, name="update"),
    path('login/', login_author, name="login"),
    path('logout/', logout_author, name="logout"),
    path('<str:pk>', view_author, name="author")
]
