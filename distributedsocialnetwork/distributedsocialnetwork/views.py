from django.shortcuts import render
from author.models import Author
from post.models import Post
from friend.models import Friend, Follower
from django.conf import settings
from post.retrieval import get_detailed_post, get_public_posts
from author.retrieval import get_detailed_author, get_visible_posts
from friend.retrieval import update_friends_list


def url_convert(queryset):
    # Given queryset of authors, returns the same queryset with all urls set properly
    for obj in queryset:
        if 'api/' in obj.url:
            obj.url = obj.url.split(
                'api/')[0] + obj.url.split('api/')[-1]
    return queryset


def source_convert(queryset):
    # Same as above, but for source
    for obj in queryset:
        if 'api/' in obj.source:
            obj.source = obj.source.split(
                'api/')[0] + obj.source.split('api/')[-1]
            # Also, fix the author url
            if 'api/' in obj.author.url:
                obj.author.url = obj.author.url.split(
                    'api/')[0] + obj.author.url.split('api/')[-1]
    return queryset


def index(request):
    context = {}
    # get_public_posts()
    # for author in Author.objects.all().exclude(host=settings.FORMATTED_HOST_NAME):
    #     update_friends_list(author.id)
    # We only want the authors from our server to be featured in the "featured authors" section
    authors = Author.objects.filter(
        host=settings.FORMATTED_HOST_NAME, is_node=False, is_staff=False)
    context['authors'] = url_convert(authors)
    if request.user.is_authenticated:
        # get_visible_posts(request.user.id)
        # We give them more results on the main stream
        public_posts = Post.objects.filter(
            visibility="PUBLIC", origin__icontains=settings.FORMATTED_HOST_NAME, unlisted=False)
        # We also want to include public posts from people that this user is following, or is friends with.
        public_posts = public_posts | Post.objects.filter(
            visibility="PUBLIC", unlisted=False, author__in=(Friend.objects.get_friends(request.user) + Follower.objects.get_following(request.user)))
        user_posts = Post.objects.filter(author=request.user)
        privated_posts = Post.objects.filter(
            visibility="PRIVATE", visibleTo__icontains=request.user.id, unlisted=False)
        serveronly_posts = Post.objects.filter(
            visibility="SERVERONLY", author__in=Friend.objects.get_friends(request.user), unlisted=False)
        friend_posts = Post.objects.filter(
            visibility="FRIENDS", author__in=Friend.objects.get_friends(request.user), unlisted=False)
        foaf_posts = Post.objects.filter(
            visibility="FOAF", author__in=Friend.objects.get_foaf(request.user), unlisted=False)
        posts = public_posts | user_posts | privated_posts | serveronly_posts | friend_posts | foaf_posts
    else:
        posts = Post.objects.filter(
            visibility="PUBLIC", origin__icontains=settings.FORMATTED_HOST_NAME, unlisted=False)
    context['posts'] = source_convert(posts)
    return render(request, 'index.html', context)
