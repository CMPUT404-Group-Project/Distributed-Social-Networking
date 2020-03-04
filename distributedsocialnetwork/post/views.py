from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
import math
from django.contrib.sites.shortcuts import get_current_site

from .models import Post
from author.models import Author
# Create your views here.


def public_posts_list(request):
    # Returns all public posts on the server.
    # GET http://service/posts
    if request.method == "GET":
        # We check the request parameters to see if they have requested a specific page size
        # and/or page number
        size = 50
        page = 0
        if 'page' in request.GET.keys():
            if int(request.GET['page']) >= 0:
                page = request.GET['page']
            else:
                return HttpResponse(status=400)
        if 'size' in request.GET.keys():
            if int(request.GET['size']) >= 0:
                size = request.GET['size']
            else:
                return HttpResponse(status=400)
        # Total number of posts with PUBLIC filter
        post_count = Post.objects.filter(visibility="PUBLIC").count()
        # The number we are serving on this page
        posts = Post.objects.filter(visibility="PUBLIC")[:int(size)]

        if math.ceil(post_count / int(size)) < (int(page)+1):
            # They have requested a page which is not possible to serve.
            return HttpResponse(status=400)

        has_previous = True
        has_next = True

        if int(page) == 0:
            # There is no previous page to link to
            has_previous = False

        if (math.ceil(post_count/int(size)) - (int(page)+1)) == 0:
            # There is no next page to link to
            has_next = False

        data = {
            "query": "posts",
            "count": str(posts.count()),
            "size": str(size),
            "posts": list(posts.values(
                "title", "source", "origin", "description", "contentType", "content", "author", "categories", "size", "published", "id", "visibility", "visibleTo", "unlisted"))
        }
        if has_previous:
            data["previous"] = get_current_site(
                request).domain + request.get_full_path() + "?page=" + str(int(page) - 1) + "&size=" + str(size)

        if has_next:
            data["next"] = get_current_site(
                request).domain + request.path + "?page=" + str(int(page) + 1) + "&size=" + str(size)
        print(data)
        return JsonResponse(data)
    else:
        return HttpResponse(status=405)
