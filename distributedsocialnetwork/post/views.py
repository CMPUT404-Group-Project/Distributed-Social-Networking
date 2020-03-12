from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from .forms import PostCreationForm
from django.conf import settings
from .models import Post, Comment
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
        form = CommentCreationForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.author_id = user.id
            new_comment.origin = settings.FORMATTED_HOST_NAME + \
                'posts/' + str(new_post.id)
            new_comment.source = new_comment.origin
            new_comment.save()
    else:
        form = CommentCreationForm()

    context['post'] = get_object_or_404(Post, id=pk)
    context['post'].content = context['post'].content.splitlines()
    context['commentCreationForm'] = form
    context['comments'] = Comment.objects.filter(post_id=pk)
    return render(request, 'detailed_post.html', context)
