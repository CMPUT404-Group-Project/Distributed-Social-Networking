from rest_framework import generics, viewsets, mixins, permissions, status
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from post.models import Post, Comment
from post.serializers import PostSerializer, CommentSerializer
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

# Create your views here.


class VisiblePosts(APIView):

    # Returns a list of all public posts
    def get(self, request):
        response = {"query": "posts"}
        posts_all = Post.objects.filter(visibility='PUBLIC')
        response["count"] = len(posts_all)
        page_size = request.GET.get("size")
        if not page_size:
            page_size = 50
        response["size"] = page_size
        page_num = request.GET.get("page")
        if not page_num:
            page_num = 0
        paginator = Paginator(posts_all, page_size)
        # Paginator assumes first page is page 1, which is not to spec
        page = paginator.get_page(str(int(page_num) + 1))
        # We add links to the next and previous page, if they exist
        if page.has_next():
            response["next"] = 'http://' + \
                request.get_host() + request.path[:-1] + \
                '?size=' + str(page_size) + '&page=' + str(int(page_num) + 1)
        if page.has_previous():
            response["previous"] = 'http://' + request.get_host() + request.path[:-1] + \
                '?size=' + str(page_size) + '&page=' + str(int(page_num) - 1)

        # The serializer takes care of a lot of this stuff, but we will need to add
        # certain things (comments, etc) to each page before we add them to the response
        serializer = PostSerializer(page, many=True)
        serialized_posts = serializer.data
        for post in serialized_posts:
            post['size'] = page_size
            comments_all = Comment.objects.filter(post_id=post["id"])
            post['count'] = len(comments_all)
            post['next'] = 'http://' + request.get_host() + request.path + \
                post["id"] + '/comments'
            comment_paginator = Paginator(comments_all, page_size)
            comment_page = comment_paginator.get_page(1)
            post['comments'] = CommentSerializer(comment_page, many=True).data

            # Both visibleTo and categories are charfields
            # We split on ',' for these
            if post['visibleTo'] == "":
                # Not set, so "" by default
                post['visibleTo'] = []
            else:
                post['visibleTo'] = post['visibleTo'].split(',')
            if post['categories'] == "":
                post['categories'] = []
            else:
                post['categories'] = post['categories'].split(',')

        response["posts"] = serialized_posts
        return Response(response)


class PostDetailView(APIView):
    # Retrieving the detailed view of a single post
    # The example article says this needs to be a list of one.
    def get(self, request, pk):
        response = {"query": "posts"}
        posts_all = Post.objects.filter(id=pk)
        response["count"] = len(posts_all)
        page_size = request.GET.get("size")
        if not page_size:
            page_size = 50
        response["size"] = page_size
        page_num = request.GET.get("page")
        if not page_num:
            page_num = 0
        paginator = Paginator(posts_all, page_size)
        # Paginator assumes first page is page 1, which is not to spec
        page = paginator.get_page(str(int(page_num) + 1))
        # We add links to the next and previous page, if they exist
        if page.has_next():
            response["next"] = 'http://' + \
                request.get_host() + request.path[:-1] + \
                '?size=' + str(page_size) + '&page=' + str(int(page_num) + 1)
        if page.has_previous():
            response["previous"] = 'http://' + request.get_host() + request.path[:-1] + \
                '?size=' + str(page_size) + '&page=' + str(int(page_num) - 1)

        # The serializer takes care of a lot of this stuff, but we will need to add
        # certain things (comments, etc) to each page before we add them to the response
        serializer = PostSerializer(page, many=True)
        serialized_posts = serializer.data
        for post in serialized_posts:
            post['size'] = page_size
            comments_all = Comment.objects.filter(post_id=post["id"])
            post['count'] = len(comments_all)
            post['next'] = 'http://' + request.get_host() + request.path + \
                'comments'
            comment_paginator = Paginator(comments_all, page_size)
            comment_page = comment_paginator.get_page(1)
            post['comments'] = CommentSerializer(comment_page, many=True).data

            # Both visibleTo and categories are charfields
            # We split on ',' for these
            if post['visibleTo'] == "":
                # Not set, so "" by default
                post['visibleTo'] = []
            else:
                post['visibleTo'] = post['visibleTo'].split(',')
            if post['categories'] == "":
                post['categories'] = []
            else:
                post['categories'] = post['categories'].split(',')

        response["posts"] = serialized_posts
        return Response(response)

    def post(self, request, pk):
        # This is used for two different purposes:
        # 1) Adding a new post
        # 2) Requesting a post for FOAF purposes
        # The latter involves the friends system, which is not implemented.
        # The documentation does not specify what the POSTing a Post is supposed to look like.
        # I assume that it is similar to
        pass


class CommentList(APIView):
    def get(self, request, pk):
        response = {"query": "comments"}
        comments_all = Comment.objects.filter(post_id=pk)
        response["count"] = len(comments_all)
        page_size = request.GET.get("size")
        if not page_size:
            page_size = 50
        response["size"] = page_size
        page_num = request.GET.get("page")
        if not page_num:
            page_num = 0
        paginator = Paginator(comments_all, page_size)
        # Paginator assumes first page is page 1, which is not to spec
        page = paginator.get_page(str(int(page_num) + 1))
        # We add links to the next and previous page, if they exist
        if page.has_next():
            response["next"] = 'http://' + \
                request.get_host() + request.path + \
                '?size=' + str(page_size) + '&page=' + str(int(page_num) + 1)
        if page.has_previous():
            response["previous"] = 'http://' + request.get_host() + request.path + \
                '?size=' + str(page_size) + '&page=' + str(int(page_num) - 1)
        serializer = CommentSerializer(page, many=True)
        serialized_posts = serializer.data
        response["comments"] = serialized_posts
        return Response(response)

    def post(self, request, pk):
        if request.headers["Content-Type"] == 'application/json':
            # We insert a comment to this post's comments
            comment = request.data["comment"]
            # Our comment model has an author field that is just an ID. So we have to strip that out
            comment["author"] = comment["author"]["id"]
            serializer = CommentSerializer(
                data=comment, context={'request': request, "pk": pk})
            if serializer.is_valid():
                serializer.create(serializer.validated_data)
                return Response({
                    "query": "addComment",
                    "success": True,
                    "message": "Comment Added"
                }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
