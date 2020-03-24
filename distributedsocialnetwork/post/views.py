from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from .forms import PostCreationForm, PostCommentForm
from django.conf import settings
from .models import Post, Comment
from friend.models import Friend
from author.models import Author
import datetime
import uuid
from .retrieval import get_detailed_post
# Create your views here.


def create_post(request):
    context = {}

    user = request.user
    if not user.is_authenticated:
        return redirect(reverse_lazy('login'))

    if request.POST:
        form = PostCreationForm(request.POST)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author_id = user.id
            new_post.origin = settings.FORMATTED_HOST_NAME + \
                'posts/' + str(new_post.id)
            new_post.source = new_post.origin
            new_post.save()
            return redirect(new_post.source)

    else:
        form = PostCreationForm()

    context['postCreationForm'] = form
    return render(request, 'create.html', context)


def view_post(request, pk):
    context = {}
    if request.POST:
        if request.user.is_authenticated:
            form = PostCommentForm(request.POST)
            if form.is_valid():
                new_comment = form.save(commit=False)
                new_comment.author_id = request.user.id
                new_comment.published = datetime.datetime.now()
                new_comment.id = uuid.uuid4().hex
                new_comment.post_id = get_object_or_404(Post, id=pk)
                new_comment.save()
                return redirect(new_comment.post_id.source)
            else:
                form = PostCommentForm()
    else:
        form = PostCommentForm()

    context['post'] = get_detailed_post(post_id=pk)
    print(type(context['post']))
    # Now that we have the post in the backend, we have to verify that the current user can see it.
    post_visibility = context["post"].visibility
    if post_visibility != "PUBLIC":
        # Only certain people can see this post
        if not request.user.is_authenticated:
            return redirect(reverse_lazy('home'))
        if post_visibility == "PRIVATE":
            if request.user.id not in context["post"].visibleTo and request.user.id != context["post"].author_id:
                return redirect(reverse_lazy('home'))
        if post_visibility == "FOAF":
            if request.user not in Friend.objects.get_foaf(
                    get_object_or_404(Author, id=context["post"].author_id)) and request.user.id != context["post"].author_id:
                return redirect(reverse_lazy('home'))
        if post_visibility == "FRIENDS":
            if request.user not in Friend.objects.get_friends(get_object_or_404(Author, id=context["post"].author_id)) and request.user.id != context["post"].author_id:
                return redirect(reverse_lazy('home'))
        if post_visibility == "SERVERONLY":
            # For now, since these posts are only on one server, we ONLY check if they are friends
            if request.user not in Friend.objects.get_friends(get_object_or_404(Author, id=context["post"].author_id)) and request.user.id != context["post"].author_id:
                return redirect(reverse_lazy('home'))

    context['edit_url'] = request.get_full_path() + '/edit'
    context["request"] = request
    context['postCommentForm'] = form
    context['comments'] = Comment.objects.filter(post_id=pk)
    return render(request, 'detailed_post.html', context)


def edit_post(request, pk):
    # The same as creating a post, we just pass the instance into the form
    context = {}

    user = request.user
    if not user.is_authenticated:
        return redirect(reverse_lazy('login'))

    post = get_object_or_404(Post, id=pk)
    if post.author_id != user.id:
        # There is no point continuing. Redirect them back to the post detail page.
        return redirect(post.source)

    # They are authenticated, and they are the author of this post. We can continue.
    if request.POST:
        form = PostCreationForm(request.POST, instance=post)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author_id = user.id
            new_post.origin = settings.FORMATTED_HOST_NAME + \
                'posts/' + str(new_post.id)
            new_post.source = new_post.origin
            new_post.save()
            return redirect(new_post.source)

    else:
        form = PostCreationForm(instance=post)

    context['postCreationForm'] = form
    return render(request, 'edit_post.html', context)


def delete_post(request, pk):
    # This is a confirmation page to give the author one last chance to cancel the deletion of the post.
    # We DO NOT want other users to be able to access this page and delete the posts of someone else
    user = request.user
    if not user.is_authenticated:
        return redirect(reverse_lazy('login'))
    post = get_object_or_404(Post, id=pk)
    if not user.id == post.author_id:
        # They have no business being here, leave please
        return redirect(post.source)
    if request.POST:
        # They have opted to delete the post.
        # For safety's sake, one last check to confirm they are the right user:
        if request.user.id == post.author_id:
            Post.objects.get(id=pk).delete()
        return redirect(reverse_lazy('home'))
    context = {}
    context["request"] = request
    context["post"] = post
    comment_count = len(Comment.objects.filter(post_id=pk))
    context["comment_count"] = comment_count
    return render(request, 'delete_confirmation.html', context)
