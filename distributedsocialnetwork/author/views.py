from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse_lazy
from django.http import HttpResponseNotFound

from .forms import AuthorCreationForm, AuthorChangeForm, AuthorAuthenticationForm
from .models import Author
from .retrieval import get_detailed_author
from post.models import Post
from friend.models import Friend, Follower


def index(request):
    context = {}

    authors = Author.objects.all()
    context['authors'] = authors

    return render(request, 'index.html', context)


def create_author(request):
    context = {}

    if request.POST:
        form = AuthorCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse_lazy('home'))
        else:
            context['form'] = form

    else:
        form = AuthorCreationForm()
        context['form'] = form

    return render(request, 'register.html', context)


def change_author(request):
    if not request.user.is_authenticated:
        return redirect(reverse_lazy('login'))

    context = {}

    if request.POST:
        form = AuthorChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            url_segments = request.user.id.split('/')
            user_id = url_segments[-1]
            return redirect(reverse_lazy('author', args=[user_id]))
    else:
        form = AuthorChangeForm(
            initial={
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "github": request.user.github,
            }
        )

    context['updateForm'] = form
    return render(request, 'update.html', context)


def login_author(request):
    context = {}

    user = request.user
    if user.is_authenticated:
        return redirect(reverse_lazy('home'))

    if request.POST:
        form = AuthorAuthenticationForm(request.POST)
        if form.is_valid():
            display_name = request.POST['displayName']
            password = request.POST['password']
            user = authenticate(displayName=display_name, password=password)

            if user:
                login(request, user)
                return redirect(reverse_lazy('home'))
    else:
        form = AuthorAuthenticationForm()

    context['loginForm'] = form
    return render(request, 'login.html', context)


def logout_author(request):
    # Logout via a GET is problematic, despite Django doing so by default. So we now do so via POST.
    if request.method == "POST":
        if request.user.is_authenticated:
            if request.user.displayName == request.POST.get("displayName"):
                logout(request)
        return redirect(reverse_lazy('home'))
    # If someone tries to GET the page we return a 404
    return HttpResponseNotFound()


def view_author(request, pk):
    context = {}
    context['author'] = get_detailed_author(Author_id=pk)
    if request.method == "GET":
        context["friendrequest"] = "DISABLED"
        if request.user.is_authenticated:
            context["user"] = request.user
            context["friendrequest"] = "ENABLED"
            if request.user.id == context["author"].id or Friend.objects.are_friends(request.user, context["author"]):
                # They should not be able to send a friend request
                context["friendrequest"] = "DISABLED"
            if Follower.objects.is_following(request.user, context["author"]):
                # We have already sent a friend request
                context["friendrequest"] = "PENDING"
            if Follower.objects.is_followed_by(request.user, context["author"]):
                # We should make the button accept the friend request instead
                context["friendrequest"] = "FOLLOWED"
            # We will show different posts depending on if the user is logged in and authenticated
            if request.user.id == context["author"].id:
                # The user is logged in, so they should be able to see all of their posts
                context["posts"] = Post.objects.filter(
                    author=context["author"].id)
            else:
                # We return the posts this user can see
                author_public_posts = Post.objects.filter(
                    author=context["author"].id, visibility="PUBLIC")
                author_private_posts = Post.objects.filter(
                    author=context["author"].id, visibility="PRIVATE", visibleTo__icontains=request.user.id)
                post_query_set = author_private_posts | author_public_posts
                if Friend.objects.are_friends(context["author"], request.user):
                    # They are friends, so they can see some other posts
                    serveronly_posts = Post.objects.filter(
                        visibility="SERVERONLY", author=context["author"].id)
                    friend_posts = Post.objects.filter(
                        visibility="FRIENDS", author=context["author"].id)
                    # They are friends, so they have to get FOAF posts
                    foaf_posts = Post.objects.filter(
                        visibility="FOAF", author=context["author"].id)
                    post_query_set = post_query_set | serveronly_posts | friend_posts | foaf_posts
                context["posts"] = post_query_set
        else:
            context['posts'] = Post.objects.filter(
                author=context['author'].id, visibility="PUBLIC")
            context["user"] = None
    if request.method == "POST":
        # A post here is when we are going to send a friend request from the currently authenticated user
        if request.user.is_authenticated:
            # This should be true, but in case it is not
            user = request.user
            if not Friend.objects.are_friends(user, context["author"]):
                if Follower.objects.is_followed_by(user, context["author"]):
                    # The have sent us a friend request, so the POST is to accept it
                    Friend.objects.add_friend(user, context["author"])
                    return redirect(request.path)
                else:
                    if not Follower.objects.is_following(user, context["author"]):
                        # Checking that they are not friends, and that we have not already sent a friend request
                        Follower.objects.add_follower(user, context["author"])
                    return redirect(request.path)
        # If they sent a post but aren't authenticated we redirect them back to the page
        return redirect(request.path)
    return render(request, 'detailed_author.html', context)
