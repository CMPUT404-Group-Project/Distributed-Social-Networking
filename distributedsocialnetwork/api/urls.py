"""distributedsocialnetwork URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from .views import PostDetailView, CommentList, VisiblePosts, AuthUserPosts, AuthorPosts, AuthorFriendsList, AreAuthorsFriends


urlpatterns = [
    path('posts/', VisiblePosts.as_view(), name='public-posts'),
    path('posts/<uuid:pk>/', PostDetailView.as_view(), name="posts-detail"),
    path('posts/<uuid:pk>/comments',
         CommentList.as_view(), name="comments-list"),
    path('author/posts/', AuthUserPosts.as_view(), name="auth-posts"),
    path('author/<str:pk>/posts', AuthorPosts.as_view(), name="author-posts"),
    path('author/<str:pk>/friends',
         AuthorFriendsList.as_view(), name="author-friends"),
    path('author/<str:pk>/friends/<str:service>/author/<str:author2_id>',
         AreAuthorsFriends.as_view(), name='are-authors-friends'),
]
