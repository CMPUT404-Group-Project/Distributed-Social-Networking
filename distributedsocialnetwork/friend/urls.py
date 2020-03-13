from django.urls import path
from .views import show_friends, unfollow_author, follow_author, remove_friend, accept_request, reject_request

urlpatterns = [
    path('', show_friends, name='friends_root'),
    path('follow', follow_author, name='follow_author'),
    path('accept', accept_request, name='accept_request'),
    path('reject', reject_request, name='reject_request'),
    path('unfriend', remove_friend, name='remove_friend'),
    path('unfollow', unfollow_author, name='unfollow_author')
]