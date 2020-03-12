from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse_lazy

from .forms import AuthorCreationForm, AuthorChangeForm, AuthorAuthenticationForm
from .models import Author
from post.models import Post
from friend.models import Friend


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
            return redirect(reverse_lazy('home'))
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
    logout(request)
    return redirect(reverse_lazy('home'))


def view_author(request, pk):
    context = {}
    context['author'] = get_object_or_404(Author, id__icontains=pk)
    if request.user.is_authenticated:
        context["user"] = request.user
        # We will show different posts depending on if the user is logged in and authenticated
        if request.user.id == context["author"].id:
            # The user is logged in, so they should be able to see all of their posts
            context["posts"] = Post.objects.filter(author=context["author"].id)
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
    return render(request, 'detailed_author.html', context)
