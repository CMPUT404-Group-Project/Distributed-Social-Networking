from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

from .models import Post
from author.models import Author
# Create your views here.


def public_posts_list(request):
    # Returns all public posts on the server.
    # GET http://service/posts
    if request.method == "GET":
        DEFAULT_SIZE = 50
        posts = Post.objects.filter(visibility="PUBLIC")
        data = {"results": list(posts.values("title",
                                             "source", "origin", "description", "contentType", "content", "author",
                                             "categories", "size", "published", "id", "visibility", "visibleTo", "unlisted"))}
        return JsonResponse(data)
