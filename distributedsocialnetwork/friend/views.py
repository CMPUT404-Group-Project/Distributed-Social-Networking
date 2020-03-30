from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.conf import settings
from friend.models import FollowerManager, FriendManager, Follower
from author.models import Author
from django.conf import settings
from .retrieval import send_friend_request
# This is a tool to convert urls into links that work
from distributedsocialnetwork.views import url_convert

# Create your views here.

# This one is not a view.


def show_friends(request):
    context = {}
    current_user = request.user
    if not current_user.is_authenticated:
        return redirect(reverse_lazy('login'))

    user_id = current_user.id
    followers = FollowerManager.get_followers('', user_id)
    following = FollowerManager.get_following('', user_id)
    friends = FriendManager.get_friends('', user_id)
    context['friends'] = url_convert(friends)
    context['followers'] = url_convert(followers)
    context['following'] = url_convert(following)

    # non-fff
    # Everyone now excludes nodes, admins
    local = url_convert(Author.objects.filter(
        is_node=False, is_staff=False, host=settings.FORMATTED_HOST_NAME))
    # Foreign is everyone who is not local
    foreign = url_convert(Author.objects.filter(is_node=False, is_staff=False).exclude(
        host=settings.FORMATTED_HOST_NAME))
    fff = set([current_user] + followers + following + friends)
    other_local = []
    other_foreign = []
    for author in local:
        if author not in fff:
            other_local.append(author)
    for author in foreign:
        if author not in fff:
            other_foreign.append(author)
    context['local'] = local
    context['other_local'] = other_local
    context['foreign'] = foreign
    context['other_foreign'] = other_foreign
    context['hostname'] = settings.FORMATTED_HOST_NAME
    return render(request, 'friends.html', context)


def follow_author(request):
    # follow local author
    if request.method == "POST":
        current_user = request.user
        to_follow_id = request.POST["authorId"]
        to_follow = Author.objects.filter(id=to_follow_id)[0]
        if to_follow.host == settings.FORMATTED_HOST_NAME:
            FollowerManager.add_follower("", current_user, to_follow)
            return redirect(show_friends)
        else:
            response = send_friend_request(current_user.id, to_follow_id)
            if response.status_code == 200:
                # Successful, we are good to go
                FollowerManager.add_follower("", current_user, to_follow)
                return redirect(show_friends)
            else:
                print(response.status_code)
                return redirect(show_friends)

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
        if to_friend.host != settings.FORMATTED_HOST_NAME:
            # They are a foreign author, so we have to send a friend request via the API
            response = send_friend_request(current_user.id, to_friend_id)
            if response.status_code == 200:
                # Successful, we are good to go
                FriendManager.add_friend("", current_user, to_friend)
                return redirect(show_friends)
            else:
                # We can't add them as a friend right now.
                # TODO: Popup message saying there was an error
                print(response.status_code)
                return redirect(show_friends)
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
