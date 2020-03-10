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
import urllib
# Create your views here.

# The following are some tools for paginating and generating a lot of the nitty gritty details of GET responses
# involving lists of posts and comments


def post_list_generator(request, query_set):
    # Given a request, a QuerySet of Posts, and the base URL for which to add page and size parameters,
    # returns a dict containing the size, page number, link to next, link to previous, and the list of serialized posts
    page_size = request.GET.get("size") or 50
    page_num = request.GET.get("page") or 0
    count = len(query_set)
    paginator = Paginator(query_set, page_size)
    page = paginator.get_page(str(int(page_num) + 1))
    path = request.path
    if path[-1] == '/':
        # Django adds trailing backslashes, sometimes inconsistently.
        path = path[:-1]
    if page.has_next():
        next_link = 'http://' + \
            request.get_host() + path + \
            '?size=' + str(page_size) + '&page=' + str(int(page_num) + 1)
    else:
        next_link = None
    if page.has_previous():
        previous_link = 'http://' + request.get_host() + path + \
            '?size=' + str(page_size) + '&page=' + str(int(page_num) - 1)
    else:
        previous_link = None
    post_serializer = PostSerializer(page, many=True)
    for post in post_serializer.data:
        # We have to split the categories and visible_to fields
        if post['visibleTo'] == "":
            # Not set, so "" by default
            post['visibleTo'] = []
        else:
            post['visibleTo'] = post['visibleTo'].split(',')
        if post['categories'] == "":
            post['categories'] = []
        else:
            post['categories'] = post['categories'].split(',')
    return {
        "page_size": page_size,
        "page_num": page_num,
        "count": count,
        "next": next_link,
        "previous": previous_link,
        "posts": post_serializer.data
    }


def nested_comment_list_generator(request, query_set, post_id):
    # Given a request, a QuerySet of comments, and the post id of the comment set,
    # returns a dict containing the size, link to all comments, and the list of serialized comments
    page_size = request.GET.get("size") or 5
    count = len(query_set)
    paginator = Paginator(query_set, page_size)
    page = paginator.get_page(1)
    next_link = 'http://' + request.get_host() + '/api/posts/' + \
        post_id + '/comments'
    comment_serializer = CommentSerializer(page, many=True)
    for comment in comment_serializer.data:
        # We don't need to include the post id when dealing with nested comment lists
        comment.pop('post_id')
    return {
        "page_size": page_size,
        "count": count,
        "next": next_link,
        "comments": comment_serializer.data
    }


def comment_list_generator(request, query_set):
    # Given a request, a QuerySet of comments, and the post id of the comment set,
    # returns a dict containing the size, page number, next link, previous link, and list of serialized comments
    page_size = request.GET.get("size") or 50
    page_num = request.GET.get("page") or 0
    count = len(query_set)
    paginator = Paginator(query_set, page_size)
    page = paginator.get_page(str(int(page_num) + 1))
    path = request.path
    if path[-1] == '/':
        # Django adds trailing backslashes, sometimes inconsistently.
        path = path[:-1]
    if page.has_next():
        next_link = 'http://' + \
            request.get_host() + path + \
            '?size=' + str(page_size) + '&page=' + str(int(page_num) + 1)
    else:
        next_link = None
    if page.has_previous():
        previous_link = 'http://' + request.get_host() + path + \
            '?size=' + str(page_size) + '&page=' + str(int(page_num) - 1)
    else:
        previous_link = None
    comment_serializer = CommentSerializer(page, many=True)
    return {
        "page_size": page_size,
        "page_num": page_num,
        "count": count,
        "next": next_link,
        "previous": previous_link,
        "comments": comment_serializer.data
    }


class VisiblePosts(APIView):

    # Returns a list of all public posts
    def get(self, request):
        response = {"query": "posts"}
        post_query_set = Post.objects.filter(visibility="PUBLIC")
        post_list_dict = post_list_generator(request, post_query_set)
        # Returns [page_size, page_num, count, next_link, previous_link, serialized posts]
        response["count"] = post_list_dict["count"]
        response["size"] = post_list_dict["page_size"]
        if post_list_dict["next"]:
            response["next"] = post_list_dict["next"]
        if post_list_dict["previous"]:
            response["previous"] = post_list_dict["previous"]
        # We add nested comment lists for all posts
        for post in post_list_dict["posts"]:
            comment_query_set = Comment.objects.filter(post_id=post["id"])
            comment_list_dict = nested_comment_list_generator(
                request, comment_query_set, post["id"])
            post["count"] = comment_list_dict["count"]
            post["next"] = comment_list_dict["next"]
            post["comments"] = comment_list_dict["comments"]
        response["posts"] = post_list_dict["posts"]
        return Response(response)

# ====== /api/posts/<post_id> ======


class PostDetailView(APIView):
    # Retrieving the detailed view of a single post
    # The example article says this needs to be a list of one.
    def get(self, request, pk):
        response = {"query": "posts"}
        post_query_set = Post.objects.filter(id=pk)
        post_list_dict = post_list_generator(request, post_query_set)
        # Returns [page_size, page_num, count, next_link, previous_link, serialized posts]
        response["count"] = post_list_dict["count"]
        response["size"] = post_list_dict["page_size"]
        if post_list_dict["next"]:
            response["next"] = post_list_dict["next"]
        if post_list_dict["previous"]:
            response["previous"] = post_list_dict["previous"]
        # We add nested comment lists for all posts
        for post in post_list_dict["posts"]:
            comment_query_set = Comment.objects.filter(post_id=post["id"])
            comment_list_dict = nested_comment_list_generator(
                request, comment_query_set, post["id"])
            post["count"] = comment_list_dict["count"]
            post["next"] = comment_list_dict["next"]
            post["comments"] = comment_list_dict["comments"]
        response["posts"] = post_list_dict["posts"]
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
                post["visibleTo"] = ','.join(post["categories"])
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
            except Exception as e:
                # We can't parse the body
                return Response({
                    "query": "addPost",
                    "success": False,
                    "message": "Body is incorrectly formatted. " + str(e)
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
                post["visibleTo"] = ','.join(post["visibleTo"])
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
            except Exception as e:
                # We can't parse the body
                return Response({
                    "query": "updatePost",
                    "success": False,
                    "message": "Body is incorrectly formatted. " + str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "query": "updatePost",
            "success": False,
            "message": ("Must be of type application/json. Type was " + str(request.headers["Content-Type"]))}, status=status.HTTP_400_BAD_REQUEST)

# ====== /api/posts/<post_id>/comments ======


class CommentList(APIView):
    def get(self, request, pk):
        response = {"query": "comments"}
        comment_query_set = Comment.objects.filter(post_id=pk)
        comment_list_dict = comment_list_generator(request, comment_query_set)
        response["count"] = comment_list_dict["count"]
        response["size"] = comment_list_dict["page_size"]
        if comment_list_dict["next"]:
            response["next"] = comment_list_dict["next"]
        if comment_list_dict["previous"]:
            response["previous"] = comment_list_dict["previous"]
        response["comments"] = comment_list_dict["comments"]
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
        # The url is now a fragment of the Author's ID. We need to retrieve the appropriate author object.
        response = {'query': "posts"}
        if request.user.is_authenticated:
            # The user is logged in, so we send them all posts they can see
            public_posts = Post.objects.filter(visibility="PUBLIC")
            user_posts = Post.objects.filter(author=request.user)
            privated_posts = Post.objects.filter(
                visibility="PRIVATE", visibleTo__icontains=request.user.id)
            post_query_set = public_posts | user_posts | privated_posts
        else:
            # They are not logged in and authenticated. So
            post_query_set = Post.objects.filter(visibility="PUBLIC")
        post_list_dict = post_list_generator(request, post_query_set)
        # Returns [page_size, page_num, count, next_link, previous_link, serialized posts]
        response["count"] = post_list_dict["count"]
        response["size"] = post_list_dict["page_size"]
        if post_list_dict["next"]:
            response["next"] = post_list_dict["next"]
        if post_list_dict["previous"]:
            response["previous"] = post_list_dict["previous"]
        # We add nested comment lists for all posts
        for post in post_list_dict["posts"]:
            comment_query_set = Comment.objects.filter(post_id=post["id"])
            comment_list_dict = nested_comment_list_generator(
                request, comment_query_set, post["id"])
            post["count"] = comment_list_dict["count"]
            post["next"] = comment_list_dict["next"]
            post["comments"] = comment_list_dict["comments"]
        response["posts"] = post_list_dict["posts"]
        return Response(response)

# ====== /api/author/posts/<author_id>/posts ======


class AuthorPosts(APIView):
    # Returns all posts from the specified author that the currently authenticated user can see
    def get(self, request, pk):
        # The URL contains a fragment of the specified author's id. We have to retrieve the actual author.
        author = get_object_or_404(Author, id__icontains=pk)
        author_id = author.id
        response = {"query": "posts"}
        if request.user.is_authenticated:
            if author_id == request.user.id:
                # This is the author, they should be able to see all their posts
                post_query_set = Post.objects.filter(author=author_id)
            else:
                # The user is logged in, so we return all public posts and private posts they have been shared with posted by this author
                author_public_posts = Post.objects.filter(
                    author=author_id, visibility="PUBLIC")
                author_private_posts = Post.objects.filter(
                    author=author_id, visibility="PRIVATE", visibleTo__icontains=request.user.id)
                post_query_set = author_public_posts | author_private_posts
        else:
            post_query_set = Post.objects.filter(
                author=author_id, visibility="PUBLIC")
        post_list_dict = post_list_generator(request, post_query_set)
        # Returns [page_size, page_num, count, next, previous, posts]
        response["count"] = post_list_dict["count"]
        response["size"] = post_list_dict["page_size"]
        if post_list_dict["next"]:
            response["next"] = post_list_dict["next"]
        if post_list_dict["previous"]:
            response["previous"] = post_list_dict["previous"]
        # We add nested comment lists for all posts
        for post in post_list_dict["posts"]:
            comment_query_set = Comment.objects.filter(post_id=post["id"])
            comment_list_dict = nested_comment_list_generator(
                request, comment_query_set, post["id"])
            post["count"] = comment_list_dict["count"]
            post["next"] = comment_list_dict["next"]
            post["comments"] = comment_list_dict["comments"]
        response["posts"] = post_list_dict["posts"]
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


class AreAuthorsFriends(APIView):
    # GET returns a list of both authors if they are friends, and none if they are not
    def get(self, request, pk, service, author2_id):
        other_user_id = "http://" + service + '/author/' + author2_id
        response = {"query": "friends"}
        author1 = get_object_or_404(Author, id__icontains=pk)
        author2 = get_object_or_404(Author, id=other_user_id)
        response["authors"] = [author1.id, author2.id]
        response["friends"] = False
        if Friend.objects.are_friends(author1, author2):
            response["friends"] = True
        return Response(response, status=status.HTTP_200_OK)
