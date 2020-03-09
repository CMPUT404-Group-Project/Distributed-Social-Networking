from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from post.models import Post, Comment
from author.models import Author
from friend.models import Friend, Follower
from post.serializers import PostSerializer, CommentSerializer
from django.core.paginator import Paginator
from django.urls import reverse
from django.shortcuts import get_object_or_404
# Create your views here.

# ====== /api/posts ======


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
            serialized_comments = CommentSerializer(
                comment_page, many=True).data
            for comment in serialized_comments:
                comment.pop('post_id')
            post['comments'] = serialized_comments

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

# ====== /api/posts/<post_id> ======


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
        # certain things (comments, etc) to each post before we add them to the response
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
            serialized_comments = CommentSerializer(
                comment_page, many=True).data
            for comment in serialized_comments:
                comment.pop('post_id')
            post['comments'] = serialized_comments

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
        # So I assume it is similar to posting a comment.
        if 'application/json' in request.headers["Content-Type"]:
            if request.data["query"] == "friends":
                # FOAF stuff to be added here (once we have friends)
                pass
            try:
                post = request.data["post"]
                # Author gets collapsed to author's id
                post["author"] = post["author"]["id"]
                post["id"] = pk
                post["categories"] = ','.join(post["categories"])
                serializer = PostSerializer(
                    data=post, context={"request": request})
                if serializer.is_valid():
                    try:
                        serializer.create(serializer.validated_data)
                        return Response({
                            "query": "addPost",
                            "success": True,
                            "message": "Post Added"
                        }, status=status.HTTP_201_CREATED)
                    except:
                        # Failed to create, because that post id is already in use.
                        # Posts can be updated, but they should be using PUT for this.
                        return Response({
                            "query": "addPost",
                            "success": False,
                            "message": "Post ID already exists."
                        }, status=status.HTTP_403_FORBIDDEN)
                return Response({
                    "query": "addPost",
                    "success": False,
                    "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            except:
                # We can't parse the body
                return Response({
                    "query": "addPost",
                    "success": False,
                    "message": "Body is incorrectly formatted."
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "query": "addPost",
            "success": False,
            "message": ("Must be of type application/json. Type was " + str(request.headers["Content-Type"]))}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        # Updating the post that is at this URI
        if 'application/json' in request.headers["Content-Type"]:
            try:
                post = request.data["post"]
                # Author gets collapsed to author's id
                post["author"] = post["author"]["id"]
                post["id"] = pk
                post["categories"] = ','.join(post["categories"])
                post_to_update = Post.objects.filter(id=pk)[0]
                serializer = PostSerializer(instance=post_to_update, data=post)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        "query": "updatePost",
                        "success": True,
                        "message": "Post Updated"
                    }, status=status.HTTP_200_OK)
                return Response({
                    "query": "updatePost",
                    "success": False,
                    "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            except:
                # We can't parse the body
                return Response({
                    "query": "updatePost",
                    "success": False,
                    "message": "Body is incorrectly formatted."
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "query": "updatePost",
            "success": False,
            "message": ("Must be of type application/json. Type was " + str(request.headers["Content-Type"]))}, status=status.HTTP_400_BAD_REQUEST)

# ====== /api/posts/<post_id>/comments ======


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
        serialized_comments = serializer.data
        for comment in serialized_comments:
            comment.pop('post_id')
        response["comments"] = serialized_comments
        return Response(response)

    def post(self, request, pk):
        if 'application/json' in request.headers["Content-Type"]:
            try:
                # We insert a comment to this post's comments
                comment = request.data["comment"]
                # Our comment model has an author field that is just an ID. So we have to strip that out
                comment["author"] = comment["author"]["id"]
                # We use the pk in the url for the post_id.
                comment["post_id"] = pk
                serializer = CommentSerializer(
                    data=comment, context={'request': request, "pk": pk})
                if serializer.is_valid():
                    try:
                        serializer.create(serializer.validated_data)
                        return Response({
                            "query": "addComment",
                            "success": True,
                            "message": "Comment Added"
                        }, status=status.HTTP_201_CREATED)
                    except:
                        # We tried to create it but the comment id is in use
                        return Response({
                            "query": "addComment",
                            "success": False,
                            "message": "Comment ID already exists."
                        }, status=status.HTTP_403_FORBIDDEN)
                return Response({
                    "query": "addComment",
                    "success": False,
                    "message": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            except:
                # We can't parse the body
                return Response({
                    "query": "addComment",
                    "success": False,
                    "message": "Body is incorrectly formatted."
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "query": "addComment",
            "success": False,
            "message": ("Must be of type application/json. Type was " + str(request.headers["Content-Type"]))}, status=status.HTTP_400_BAD_REQUEST)

# ====== /api/author/posts ======


class AuthUserPosts(APIView):
    # Returns all accessible posts for the currently authenticated user
    # If a user is authenticated:
    # * Return the public posts on this server
    # * Return the user's posts
    # * Return privated posts where the user is in the "visibleTo" list
    # * Return posts that the user's friends/people have marked as "visible to friends" (TODO: Need friends)
    # * Return posts that the user's friends of friends have visible to "friends of friends" (TODO: Need friends)

    def get(self, request):
        response = {'query': "posts"}
        if request.user.is_authenticated:
            # The user is logged in, so we send them all posts they can see
            public_posts = Post.objects.filter(visibility="PUBLIC")
            user_posts = Post.objects.filter(author=request.user)
            privated_posts = Post.objects.filter(
                visibility="PRIVATE", visibleTo__icontains=request.user.id)
            posts = public_posts | user_posts | privated_posts
        else:
            # They are not logged in and authenticated. So
            posts = Post.objects.filter(visibility="PUBLIC")
        response["count"] = len(posts)
        page_size = request.GET.get("size")
        if not page_size:
            page_size = 50
        response["size"] = page_size
        page_num = request.GET.get("page")
        if not page_num:
            page_num = 0
        paginator = Paginator(posts, page_size)
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
            post['next'] = 'http://' + request.get_host() + reverse('public-posts') + \
                post["id"] + '/comments'
            comment_paginator = Paginator(comments_all, page_size)
            comment_page = comment_paginator.get_page(1)
            serialized_comments = CommentSerializer(
                comment_page, many=True).data
            for comment in serialized_comments:
                comment.pop('post_id')
            post['comments'] = serialized_comments

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

# ====== /api/author/posts/<author_id>/posts ======


class AuthorPosts(APIView):
    # Returns all posts from the specified author that the currently authenticated user can see
    def get(self, request, pk):
        response = {"query": "posts"}
        if request.user.is_authenticated:
            if pk == request.user.id:
                # This is the author, they should be able to see all their posts
                posts = Post.objects.filter(author=pk)
            else:
                # The user is logged in, so we return all public posts and private posts they have been shared with posted by this author
                author_public_posts = Post.objects.filter(
                    author=pk, visibility="PUBLIC")
                author_private_posts = Post.objects.filter(
                    author=pk, visibility="PRIVATE", visibleTo__icontains=request.user.id)
                posts = author_public_posts | author_private_posts
        else:
            posts = Post.objects.filter(author=pk, visibility="PUBLIC")
        response["count"] = len(posts)
        page_size = request.GET.get("size")
        if not page_size:
            page_size = 50
        response["size"] = page_size
        page_num = request.GET.get("page")
        if not page_num:
            page_num = 0
        paginator = Paginator(posts, page_size)
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
            post['next'] = 'http://' + request.get_host() + reverse('public-posts') + \
                post["id"] + '/comments'
            comment_paginator = Paginator(comments_all, page_size)
            comment_page = comment_paginator.get_page(1)
            serialized_comments = CommentSerializer(
                comment_page, many=True).data
            for comment in serialized_comments:
                comment.pop('post_id')
            post['comments'] = serialized_comments

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

# ====== /api/author/<author_id>/friends ======


class AuthorFriendsList(APIView):

    def get(self, request, pk):
        # A GET request returns the list of this Author's current friends
        # We are using the django-friendship libary that handles these relationships for us
        response = {"query": "friends"}
        author = get_object_or_404(Author, id__icontains=pk)
        friends = Friend.objects.get_friends(author=author)
        response["authors"] = []
        for friend in friends:
            response["authors"].append(friend.id)
        return Response(response)

    def post(self, request, pk):
        # A POST containing an array of author ids. Respond which of these are friends of this author via JSON.
        author = get_object_or_404(Author, id__icontains=pk)
        if 'application/json' in request.headers["Content-Type"]:
            try:
                response = {"query": "friends", "author": author.id}
                response["authors"] = []
                for author_id in request.data["authors"]:
                    if Friend.objects.are_friends(author, Author.objects.get(id=author_id)):
                        response["authors"].append(author_id)
                return Response(response, status=status.HTTP_200_OK)
            except Exception as e:
                # We can't parse the body of the post request
                return Response({
                    "query": "friends",
                    "success": False,
                    "message": "Body is incorrectly formatted. " + str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "query": "friends",
            "success": False,
            "message": ("Must be of type application/json. Type was " + str(request.headers["Content-Type"]))}, status=status.HTTP_400_BAD_REQUEST)

# ====== /api/author/<author1_id>/friends/<author2_id>/ ======
