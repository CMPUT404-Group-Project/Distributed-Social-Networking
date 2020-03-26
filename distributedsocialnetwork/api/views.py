from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from post.models import Post, Comment
from author.models import Author
from friend.models import Friend, Follower
from node.models import Node
from post.serializers import PostSerializer, CommentSerializer
from author.serializers import AuthorSerializer
from django.core.paginator import Paginator
from django.urls import reverse
from django.shortcuts import get_object_or_404, render
import urllib
from django.conf import settings
import uuid

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

# ====== /api/posts ======


class VisiblePosts(APIView):
    # Returns a list of all public posts

    def get(self, request):
        response = {"query": "posts"}
        # No auth required. Send the public posts originating from this server.
        post_query_set = Post.objects.filter(
            visibility="PUBLIC", origin__icontains=settings.FORMATTED_HOST_NAME)
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

# ====== /api/posts/foreign/ ======


class ForeignPosts(APIView):
    # Retrieves all posts not originating from this server.
    # Returned as HTML for simple front-end integration.
    def get(self, request):
        posts = Post.objects.filter(visibility="PUBLIC").exclude(
            origin__icontains=settings.FORMATTED_HOST_NAME)
        context = {}
        context["posts"] = posts
        return render(request, 'stream.html', context)

# ====== /api/posts/<post_id> ======


class PostDetailView(APIView):
    # Retrieving the detailed view of a single post
    # The example article says this needs to be a list of one.
    # If this post is not Public or Unlisted, we should be authenticating in order to see it
    def get(self, request, pk):
        post_query_set = Post.objects.filter(id=pk)
        post = post_query_set[0]
        if post.visibility != "PUBLIC":
            # We can't just send it, we have to check their authentication
            if request.user.is_authenticated:
                # We can send them the post if they are.
                if request.user.is_node:
                    # They are another server, so we send the post details only if one of their users are able to see it
                    has_allowed_user = False
                    for author in list(Author.objects.filter(host=request.user.host)):
                        if Friend.objects.are_friends(author, get_object_or_404(Author, id=post.author.id)):
                            if post.visibility == "FRIENDS" or post.visibility == "FOAF":
                                has_allowed_user = True
                        if author.id in post.visibleTo and post.visibility == "PRIVATE":
                            has_allowed_user = True
                        # TODO: FOAF
                    if not has_allowed_user:
                        # They are not authenticated to see this post. We send a 401.
                        response = {
                            "query": "posts",
                            "success": False,
                            "message": "You are not authenticated to see this post."
                        }
                        return Response(response, status=status.HTTP_401_UNAUTHORIZED)
                else:
                    # They are a user, so they can see the post if they are properly authenticated
                    allowed = False
                    if Friend.objects.are_friends(request.user, get_object_or_404(Author, id=post.author_id)):
                        if post.visibility == "FRIENDS" or post.visibility == "FOAF":
                            allowed = True
                        if post.visibility == "SERVERONLY" and request.user.host == get_object_or_404(Author, id=post.author_id).host:
                            allowed = True
                    if post.visibility == "PRIVATE" and request.user.id in post.visibleTo:
                        allowed = True
                    if not allowed:
                        # They are not authenticated to see this post. We send a 401.
                        response = {
                            "query": "posts",
                            "success": False,
                            "message": "You are not authenticated to see this post."
                        }
                        return Response(response, status=status.HTTP_401_UNAUTHORIZED)
            else:
                # they can't see this post
                response = {
                    "query": "posts",
                    "success": False,
                    "message": "You are not authenticated to see this post."
                }
                return Response(response, status=status.HTTP_401_UNAUTHORIZED)
        # If they get here with no issues, they can get sent the post.
        response = {"query": "posts"}
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
        return Response(response, status=status.HTTP_200_OK)

    def post(self, request, pk):
        # This is used for two different purposes:
        # 1) Adding a new post
        # 2) Requesting a post for FOAF purposes
        # The latter involves the friends system, which is not implemented.
        # The documentation does not specify what the POSTing a Post is supposed to look like.
        # So I assume it is similar to posting a comment.
        if 'application/json' in request.headers["Content-Type"]:
            if request.data["query"] == "getPost":
                # FOAF stuff to be added here (once we have friends)
                pass
            try:
                post = request.data["post"]
                # Authors can only create posts as themselves
                if request.user.is_authenticated and request.user.id == post["author"]["id"]:
                    # Author gets collapsed to author's id
                    post["author"] = post["author"]["id"]
                    post["id"] = pk
                    post["categories"] = ','.join(post["categories"])
                    post["visibleTo"] = ','.join(post["visibleTo"])
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
                return Response({
                    "query": "addPost",
                    "success": False,
                    "message": "Not Authorized."
                }, status=status.HTTP_401_UNAUTHORIZED)
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
                # Authors can only update their own posts
                if request.user.is_authenticated and request.user.id == post["author"]["id"]:
                    # Author gets collapsed to author's id
                    post["author"] = post["author"]["id"]
                    post["id"] = pk
                    post["categories"] = ','.join(post["categories"])
                    post["visibleTo"] = ','.join(post["visibleTo"])
                    post_to_update = Post.objects.filter(id=pk)[0]
                    serializer = PostSerializer(
                        instance=post_to_update, data=post)
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
                return Response({
                    "query": "updatePost",
                    "success": False,
                    "message": "Not Authorized."
                }, status=status.HTTP_401_UNAUTHORIZED)
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

    def delete(self, request, pk):
        # Deleting the post that is at this URI and any associated comments.
        try:
            post_query_set = Post.objects.filter(id=pk)
            post = post_query_set[0]
            if request.user.is_authenticated:
                if (request.user.id == post.author.id):
                    deleted = post.delete()
                    deleted_dict = deleted[1]
                    deleted_comments = deleted_dict['post.Comment']
                    return Response({
                        "query": "deletePost",
                        "success": True,
                        "message": "Deleted post with id " + str(pk) + " and " + str(deleted_comments) + " comments."
                    })
            response = {
                "query": "deletePost",
                "success": False,
                "message": "You are not authorized to delete this post."
            }
            return Response(response, status=status.HTTP_401_UNAUTHORIZED)
        except Exception:
            # Invalid post URI
            return Response({
                "query": "deletePost",
                "success": False,
                "message": "No post with id " + str(pk) + " exists."
            }, status=status.HTTP_404_NOT_FOUND)


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
    # * Return posts that the user's friends/people have marked as "visible to friends"
    # * Return posts that the user's friends of friends have visible to "friends of friends"

    def get(self, request):
        # The url is now a fragment of the Author's ID. We need to retrieve the appropriate author object.
        response = {'query': "posts"}
        if request.user.is_authenticated:
            # We now have two different options in regards to who is authenticated.
            # 1. A user from our server
            # 2. A Node, aka another server.
            if not request.user.is_node:
                # ++++++++++++++++++++ Author from our own server is logged in +++++++++++++++++++++++
                # The user is logged in, so we send them all posts they can see
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
                post_query_set = public_posts | user_posts | privated_posts | serveronly_posts | friend_posts | foaf_posts
            else:
                # ++++++++++++++++++++ A Node is logged in +++++++++++++++++++++++++++++++++++++++++++
                # We pass over the posts that all of THEIR users can see
                # We assume that we currently have their users stored in our system.
                hostname = settings.FORMATTED_HOST_NAME
                public_posts = Post.objects.filter(
                    visibility="PUBLIC", origin__contains=hostname)
                privated_posts = Post.objects.none()
                friend_posts = Post.objects.none()
                foaf_posts = Post.objects.none()
                for author in list(Author.objects.filter(host=request.user.host)):
                    # For each author belonging to that server, we add the posts they are able to see
                    privated_posts = privated_posts | Post.objects.filter(
                        visibility="PRIVATE", visibleTo__icontains=author.id, origin__contains=hostname)
                    friend_posts = friend_posts | Post.objects.filter(
                        visibility="FRIENDS", author__in=Friend.objects.get_friends(author), origin__contains=hostname)
                    # TODO: FOAF
                post_query_set = public_posts | privated_posts | friend_posts | foaf_posts
        else:
            # They are not logged in and authenticated. So
            post_query_set = Post.objects.filter(
                visibility="PUBLIC", origin__contains=settings.FORMATTED_HOST_NAME)
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
            # We now have two different options in regards to who is authenticated.
            # 1. A user from our server
            # 2. A Node, aka another server.
            if not request.user.is_node:
                # ++++++++++++++++++++ Author from our own server is logged in +++++++++++++++++++++++
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
                    if Friend.objects.are_friends(request.user, author):
                        # We can send them a few things
                        serveronly_posts = Post.objects.filter(
                            visibility="SERVERONLY", author=author_id)
                        friend_posts = Post.objects.filter(
                            visibility="FRIENDS", author=author_id)

                        foaf_posts = Post.objects.filter(
                            visibility="FOAF", author=author_id)
                        post_query_set = post_query_set | serveronly_posts | friend_posts | foaf_posts
            else:
                # ++++++++++++++++++++ A Node is logged in +++++++++++++++++++++++++++++++++++++++++++
                # We pass over the posts that all of THEIR users can see
                # We assume that we currently have their users stored in our system.
                # We also assume they will not be querying their own user's posts
                author_public_posts = Post.objects.filter(
                    author=author_id, visibility="PUBLIC")
                author_private_posts = Post.objects.none()
                friend_posts = Post.objects.none()
                foaf_posts = Post.objects.none()
                for foreign_author in list(Author.objects.filter(host=request.user.host)):
                    # For each author belonging to that server, we add the posts they are able to see
                    author_private_posts = author_private_posts | Post.objects.filter(
                        visibility="PRIVATE", author=author_id, visibleTo__icontains=foreign_author.id)
                    if Friend.objects.are_friends(author, foreign_author):
                        friend_posts = friend_posts | Post.objects.filter(
                            visibility="FRIENDS", author=author_id)
                        foaf_posts = foaf_posts | Post.objects.filter(
                            visibility="FOAF", author=author_id)
                    # TODO: If they are FOAF.
                post_query_set = author_public_posts | author_private_posts | friend_posts | foaf_posts

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


# ====== /api/friendrequest ======
class FriendRequest(APIView):
    def post(self, request):
        # We want to send a friend request from the "author" to the "friend"
        # First off -- are they authenticated?
        if not request.user.is_authenticated:
            return Response({
                "query": "friendrequest",
                "success": False,
                "message": "Authentication is required for this endpoint."
            }, status=status.HTTP_401_UNAUTHORIZED)
        if 'application/json' in request.headers["Content-Type"]:
            try:
                # First, if we don't have any record of this person, there is no point wasting our time.
                if len(Author.objects.filter(id=request.data["friend"]["id"])) != 1:
                    return Response({
                        "query": "friendrequest",
                        "success": False,
                        "message": "The friend specified in the request body does not exist."
                    }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                # Now we check if we have any record of the author sending the request.
                if len(Author.objects.filter(id=request.data["author"]["id"])) != 1:
                    # Author does not exist in our db.
                    # If the host is different, we add it to the database.
                    # Else, we return a 400, because you should not use this to create authors with the same host
                    if request.user.is_node:
                        if request.data["author"]["host"] != settings.FORMATTED_HOST_NAME and request.data["author"]["host"] == request.user.host:
                            author = request.data["author"]
                            # We have to adjust a couple of things before we add them to our database
                            # First, they are a node, and need that node info
                            node = Node.objects.get(hostname=request.user.host)
                            author['displayName'] = author['displayName'] + \
                                ' (' + node.server_username + ')'
                            author_parts = author['id'].split('/')
                            authorID = author_parts[-1]
                            if authorID == '':
                                authorID = author_parts[-2]
                            # Our author URLS need a UUID, so we have to check if it's not
                            # The author's ID should never change!
                            try:
                                uuid.UUID(authorID)
                                author['url'] = settings.FORMATTED_HOST_NAME + \
                                    'author/' + authorID
                            except:
                                # We need to create a new one for the URL
                                if len(Author.objects.filter(id=author["id"])) == 1:
                                    # We already made one for them
                                    author['url'] = Author.objects.get(
                                        id=author["id"]).url
                                else:
                                    # Give them a new one.
                                    author['url'] = settings.FORMATTED_HOST_NAME + \
                                        'author/' + str(uuid.uuid4().hex)
                            # We try serializing and saving the author
                            author_serializer = AuthorSerializer(
                                data=author)
                            if author_serializer.is_valid():
                                author_serializer.save()
                            else:
                                # We return a 422, we can't create an author based on this data
                                return Response({
                                    "query": "friendrequest",
                                    "success": False,
                                    "message": "Author in request body cannot be deserialized."
                                }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

                        else:
                            # You can't make an author this way if you are sending this via your own Node.
                            return Response({
                                "query": "friendrequest",
                                "success": False,
                                "message": "If you are sending friend requests from this server you should be logged in as a user."
                            }, status=status.HTTP_403_FORBIDDEN)
                    else:
                        # We send a 400
                        return Response({
                            "query": "friendrequest",
                            "success": False,
                            "message": "User sending the request does not exist."
                        }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
                else:
                    # Author already exists in our system.
                    # If the user is an author, we can send the friend request if they are the one sending it
                    # If the user is a node, we send the friend request if they have the same host as the one sending it
                    if request.user.is_node:
                        if request.data["author"]["host"] != request.user.host:
                            # We send a 401. They can't send requests on behalf of users from other hosts.
                            return Response({
                                "query": "friendrequest",
                                "success": False,
                                "message": "You cannot send a friend request on behalf of a user from another service."
                            }, status=status.HTTP_401_UNAUTHORIZED)
                    else:
                        # A user is authenticated. It must be the author sending the request.
                        if request.user.id != request.data["author"]["id"]:
                            return Response({
                                "query": "friendrequest",
                                "success": False,
                                "message": "You cannot send a friend request on behalf of another user."
                            }, status=status.HTTP_401_UNAUTHORIZED)
                author = Author.objects.get(id=request.data["author"]["id"])
                friend = Author.objects.get(id=request.data["friend"]["id"])

                if not Friend.objects.are_friends(author, friend):
                    # If they are already friends, we don't need to send a friend request
                    if Follower.objects.is_following(friend, author):
                        # If we sent them a friend request, and are thus we should take this as a confirmation and add them as a friend
                        Friend.objects.add_friend(author, friend)
                        return Response({
                            "query": "friendrequest",
                            "success": True,
                            "message": "Confirmation accepted, %s and %s are now friends." % (author.displayName, friend.displayName)
                        }, status=status.HTTP_200_OK)
                    if not Follower.objects.is_following(author, friend):
                        # If a friend request has been sent then we don't need to send another
                        Follower.objects.add_follower(author, friend)
                        return Response({
                            "query": "friendrequest",
                            "success": True,
                            "message": "Friend request to %s has been sent" % friend.displayName
                        }, status=status.HTTP_200_OK)
                    # Otherwise, no point in sending one
                    return Response({
                        "query": "friendrequest",
                        "success": False,
                        "message": "%s has already sent a friend request to %s" % (author.displayName, friend.displayName)
                    }, status=status.HTTP_400_BAD_REQUEST)
                return Response({
                    "query": "friendrequest",
                    "success": False,
                    "message": "%s is already friends with %s" % (author.displayName, friend.displayName)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                # We can't parse the body of this post request
                return Response({
                    "query": "friendrequest",
                    "success": False,
                    "message": "Body is incorrectly formatted. " + str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "query": "friendrequest",
            "success": False,
            "message": ("Must be of type application/json. Type was " + str(request.headers["Content-Type"]))}, status=status.HTTP_400_BAD_REQUEST)


# ====== /api/author ======
class Authors(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({
                "query": "author",
                "success": False,
                "message": "Authentication is required for this endpoint."
            }, status=status.HTTP_401_UNAUTHORIZED)


        authors = Author.objects.filter(is_node=False, is_staff=False, host=settings.FORMATTED_HOST_NAME)
        serializer = AuthorSerializer(authors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# ====== /api/author/{author_id}/ ======


class AuthorDetail(APIView):

    def get(self, request, pk):
        # Returns the author object when requested
        author = get_object_or_404(Author, id__icontains=pk)
        # Use the serializer!
        author_serializer = AuthorSerializer(author)
        author_dict = author_serializer.data
        # We want to include friends as well, per the spec
        friend_dicts = []
        for friend in Friend.objects.get_friends(author):
            friend_dicts.append(AuthorSerializer(friend).data)
        author_dict["friends"] = friend_dicts
        response = {
            "author": author_dict
        }
        return Response(response, status=status.HTTP_200_OK)
