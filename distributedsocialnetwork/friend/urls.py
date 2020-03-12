from django.urls import path
from .views import show_followers, unfollow_author, show_following, show_friends, show_other, follow_author, remove_friend, accept_request, reject_request


urlpatterns = [
    path('', show_friends, name='friends_root'),
    path('friends', show_friends, name='show_friends'),
    path('pending', show_followers, name='show_followers'),
    path('following', show_following, name='show_following'),
    path('other', show_other, name='show_other'),
    path('follow', follow_author, name='follow_author'),
    path('accept', accept_request, name='accept_request'),
    path('reject', reject_request, name='reject_request'),
    path('unfriend', remove_friend, name='remove_friend'),
    path('unfollow', unfollow_author, name='unfollow_author')
]