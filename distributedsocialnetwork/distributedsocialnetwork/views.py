from django.shortcuts import render
from author.models import Author
from post.models import Post
from friend.models import Friend
from django.conf import settings
from post.retrieval import get_public_posts


def index(request):
    context = {}
    # We only want the authors from our server to be featured in the "featured authors" section
    authors = Author.objects.filter(
        host=settings.FORMATTED_HOST_NAME, is_node=False, is_staff=False)
    context['authors'] = authors
    if request.user.is_authenticated:
        # We give them more results on the main stream
        public_posts = Post.objects.filter(visibility="PUBLIC")
        user_posts = Post.objects.filter(author=request.user)
        privated_posts = Post.objects.filter(
            visibility="PRIVATE", visibleTo__icontains=request.user.id)
        serveronly_posts = Post.objects.filter(
            visibility="SERVERONLY", author__in=Friend.objects.get_friends(request.user))
        friend_posts = Post.objects.filter(
            visibility="FRIENDS", author__in=Friend.objects.get_friends(request.user))
        foaf_posts = Post.objects.filter(
            visibility="FOAF", author__in=Friend.objects.get_foaf(request.user))

        posts = public_posts | user_posts | privated_posts | serveronly_posts | friend_posts | foaf_posts
    else:
        posts = Post.objects.filter(visibility="PUBLIC")
    context['posts'] = posts

    return render(request, 'index.html', context)
