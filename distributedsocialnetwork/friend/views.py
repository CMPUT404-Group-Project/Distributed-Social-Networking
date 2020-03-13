from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.conf import settings
from friend.models import FollowerManager, FriendManager, Follower
from author.models import Author

# Create your views here.


def show_friends(request):
    context = {}
    current_user = request.user
    if not current_user.is_authenticated:
        return redirect(reverse_lazy('login'))

    user_id = current_user.id
    followers = FollowerManager.get_followers('', user_id)
    following = FollowerManager.get_following('', user_id)
    friends = FriendManager.get_friends('', user_id)
    context['friends'] = friends
    context['followers'] = followers
    context['following'] = following

    # non-fff
    everyone = Author.objects.all()
    fff = set([current_user] + followers + following + friends)
    others = []
    for author in everyone:
        if author not in fff:
            others.append(author)
    context['everyone'] = everyone
    context['others'] = others

    context['hostname'] = settings.FORMATTED_HOST_NAME
    return render(request, 'friends.html', context)


def follow_author(request):
    # follow local author
    if request.method == "POST":
        current_user = request.user
        to_follow_id = request.POST["authorId"]
        to_follow = Author.objects.filter(id=to_follow_id)[0]
        FollowerManager.add_follower("", current_user, to_follow)
    return redirect(show_friends)


def unfollow_author(request):
    # unfollow local author
    if request.method == "POST":
        current_user = request.user
        to_unfollow_id = request.POST["authorId"]
        unfollow = Follower.objects.filter(
            current_id=current_user.id, other_id=to_unfollow_id)
        unfollow.delete()
    return redirect(show_friends)


def accept_request(request):
    # accept friend request, removes them from followers
    if request.method == "POST":
        current_user = request.user
        to_friend_id = request.POST["authorId"]
        to_friend = Author.objects.filter(id=to_friend_id)[0]
        FriendManager.add_friend("", current_user, to_friend)
    return redirect(show_friends)


def remove_friend(request):
    # remove friend locally
    if request.method == "POST":
        current_user = request.user
        to_remove_id = request.POST["authorId"]
        to_remove = Author.objects.filter(id=to_remove_id)[0]
        FriendManager.remove_friend("", current_user, to_remove)
    return redirect(show_friends)


def reject_request(request):
    # reject friend request, equivalent to removing person as a follower
    if request.method == "POST":
        current_user = request.user
        to_reject_id = request.POST["authorId"]
        reject = Follower.objects.filter(
            current_id=to_reject_id, other_id=current_user.id)
        reject.delete()
    return redirect(show_friends)
