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
from distributedsocialnetwork.views import url_convert, source_convert
import uuid
import requests
from requests.exceptions import Timeout
from post.retrieval import sanitize_post, sanitize_author, transformSource
# Create your views here.

# The following are some tools for paginating and generating a lot of the nitty gritty details of GET responses
# involving lists of posts and comments
GLOBAL_TIMEOUT = 10


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
        posts = Post.objects.filter(visibility="PUBLIC", unlisted=False).exclude(
            origin__icontains=settings.FORMATTED_HOST_NAME)
        context = {}
        context["posts"] = source_convert(posts)
        return render(request, 'stream.html', context)

# ====== /api/posts/<post_id> ======


class PostDetailView(APIView):
    # Retrieving the detailed view of a single post
    # The example article says this needs to be a list of one.
    # If this post is not Public or Unlisted, we should be authenticating in order to see it
    def get(self, request, pk):
        post = get_object_or_404(Post, id=pk)
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
                        if post.visibility == "FOAF" and not Friend.objects.are_friends(author, get_object_or_404(Author, id=post.author.id)):
                            # If this author is friends with a friend of the post author, we can send it.
                            # We get their friends from the server
                            try:
                                node = Node.objects.get(
                                    server_username=request.user.displayName)
                                url = node.api_url + 'author/' + \
                                    author.id.split('author/')[-1] + '/friends'
                                try:
                                    response = requests.get(url, auth=(node.node_auth_username, node.node_auth_password), headers={
                                                            'content-type': 'application/json', 'Accept': 'application/json'}, timeout=GLOBAL_TIMEOUT)
                                    if response.status_code == 200:
                                        response_data = response.json()
                                        for friend_id in response_data["authors"]:
                                            # If they are friends with our author, they should be stored locally
                                            if len(Author.objects.filter(id=friend_id)) == 1:
                                                friend = Author.objects.get(
                                                    id=friend_id)
                                                if Friend.objects.are_friends(friend, get_object_or_404(Author, id=post.author.id)):
                                                    # They are FOAF. So we can send it.
                                                    has_allowed_user = True
                                except Timeout:
                                    # Request times out, so we can't send the post
                                    pass
                            except Exception:
                                # We can't reach the other server, so we can't in good conscience send this post.
                                pass

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
        response = {"query": "post"}
        post_query_set = Post.objects.filter(id=post.id)
        post_list_dict = post_list_generator(request, post_query_set)
        # Returns [page_size, page_num, count, next_link, previous_link, serialized posts]
        response["count"] = post_list_dict["count"]
        response["size"] = post_list_dict["page_size"]
        if post_list_dict["next"]:
            response["next"] = post_list_dict["next"]
        if post_list_dict["previous"]:
            response["previous"] = post_list_dict["previous"]
        # And we serialize the comments
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
        # The documentation does not specify what the POSTing a Post is supposed to look like.
        # So I assume it is similar to posting a comment.
        if 'application/json' in request.headers["Content-Type"]:
            if request.data["query"] == "getPost":
                # FOAF stuff to be added here (once we have friends)
                # A server will send us this to determine whether or not an author can see a Post
                # We check the friends they supply, querying other servers if necessary.
                # If they are indeed friends, and the post is marked as FOAF/public, then we can send it
                # First off, do we even have the post?
                post = get_object_or_404(Post, id=request.data["postid"])
                try:
                    # Now, is this person friends with everyone he says he is?
                    author_id = request.data["author"]["id"]
                    # strip off the http at the front
                    author_id = author_id.split('://')[1]
                    foaf_verified = False
                    # For each friend in the list, if we are connected, we send off a request to see if they are friends
                    for friend_id in request.data["friends"]:
                        if len(Author.objects.filter(id=friend_id)) == 1:
                            # This author is stored in our server!
                            friend = Author.objects.get(id=friend_id)
                            if friend.host == settings.FORMATTED_HOST_NAME:
                                # Friend is a user from this server. We are the absolute authority. If they are friends, we know.
                                # Which means, they must be an author in our server
                                author = Author.objects.get(id=post.author.id)
                                if Friend.objects.are_friends(author, friend):
                                    foaf_verified = True
                        if len(Node.objects.filter(hostname=friend_id.split('author')[0])) == 1:
                            # We query them
                            node = Node.objects.get(
                                hostname=friend_id.split('author')[0])
                            url = node.api_url + \
                                friend_id.split(
                                    'author/')[-1] + '/friends/' + author_id
                            try:
                                response = requests.get(url, auth=(node.node_auth_username, node.node_auth_password), headers={
                                                        'content-type': 'application/json', 'Accept': 'application/json'}, timeout=GLOBAL_TIMEOUT)
                                if response.status_code == 200:
                                    response_data = response.json()
                                    if response_data["friends"]:
                                        foaf_verified = True
                            except Exception as e:
                                # We could not reach the server, or the post was not proper JSON.
                                # We should still check the other ones
                                continue
                    if not foaf_verified:
                        # Well, they are not FOAF.
                        # However, if they can still see the post, we should be sending it anyways.
                        if post.visibility == "PUBLIC":
                            foaf_verified = True
                        if post.visibility == "PRIVATE":
                            if author_id in post.visibleTo:
                                # We can return the post
                                foaf_verified = True
                        if post.visibility == "FRIENDS":
                            # This implies that the author of the post must be friends with the author in the query
                            if len(Author.objects.filter(id=author_id)) == 1:
                                if Friend.objects.are_friends(Author.objects.get(id=author_id), Author.objects.get(id=post.author.id)):
                                    foaf_verified = True
                        if post.visibility == "SERVERONLY":
                            # If they are a user from our server, then yes
                            if author_id.split('author')[0] == settings.FORMATTED_HOST_NAME:
                                foaf_verified = True
                    if foaf_verified:
                        # They are verified to see the Post, if it is set to FOAF visibility. We return the post.
                        # But we have to check some stuff first.
                        can_send = False
                        if post.visibility in ["PUBLIC", "FOAF"]:
                            can_send = True
                        else:
                            # Despite the fact that they authenticated as FOAF, we can't return it if it's not that visibility.
                            if post.visibility == "PRIVATE":
                                if author_id in post.visibleTo:
                                    # We can return the post
                                    can_send = True
                            if post.visibility == "FRIENDS":
                                # This implies that the author of the post must be friends with the author in the query
                                if len(Author.objects.filter(id=author_id)) == 1:
                                    if Friend.objects.are_friends(Author.objects.get(id=author_id), Author.objects.get(id=post.author.id)):
                                        can_send = True
                            if post.visibility == "SERVERONLY":
                                # If they are a user from our server, then yes
                                if author_id.split('author')[0] == settings.FORMATTED_HOST_NAME:
                                    can_send = True
                        if can_send:
                            response = {"query": "post"}
                            post_query_set = Post.objects.filter(id=post.id)
                            post_list_dict = post_list_generator(
                                request, post_query_set)
                            # Returns [page_size, page_num, count, next_link, previous_link, serialized posts]
                            response["count"] = post_list_dict["count"]
                            response["size"] = post_list_dict["page_size"]
                            if post_list_dict["next"]:
                                response["next"] = post_list_dict["next"]
                            if post_list_dict["previous"]:
                                response["previous"] = post_list_dict["previous"]
                            # And we serialize the comments
                            for post in post_list_dict["posts"]:
                                comment_query_set = Comment.objects.filter(
                                    post_id=post["id"])
                                comment_list_dict = nested_comment_list_generator(
                                    request, comment_query_set, post["id"])
                                post["count"] = comment_list_dict["count"]
                                post["next"] = comment_list_dict["next"]
                                post["comments"] = comment_list_dict["comments"]
                            response["posts"] = post_list_dict["posts"]
                            return Response(response, status=status.HTTP_200_OK)
                        else:
                            response = {
                                "query": "posts",
                                "success": False,
                                "message": "You are not authenticated to see this post."
                            }
                            return Response(response, status=status.HTTP_403_FORBIDDEN)
                except Exception:
                    # Something failed here
                    response = {
                        "query": "posts",
                        "success": False,
                        "message": "Post could not be retrieved. Failure in verifying FOAF."
                    }
                    return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                # They are inserting a post
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

# ====== /api/posts/getimage ======


class GetImage(APIView):
    def post(self, request):

        # A post sends a body which is just a dict with the image link in it.
        # Should return the base64 string to embed if the user is able to see it.
        # Else, return a placeholder explaining that they can't see it.
        placeholder = "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"
        post_link = request.data['image']
        # If the user is not logged in, it will return as "None"
        # If this is the case, we make a new user and treat them as if they are a local user
        if request.data["user"] == "None":
            user = Author(id="anonymoususertemporary")
        else:
            user = Author.objects.get(id=request.data['user'])
        # We try and get the post.
        # If we have the post, check it locally.
        if len(Post.objects.filter(origin=post_link)) == 1:
            # We have it locally
            post = Post.objects.get(origin=post_link)
            if post.contentType in ['image/png;base64', 'image/jpeg;base64']:
                # It is an image, at least.
                if post.visibility == "PUBLIC":
                    return Response({"content": post.content}, status=status.HTTP_200_OK)
                if post.visibility == "PRIVATE" and (user.id in post.visibleTo or user.id == post.author.id):
                    return Response({"content": post.content}, status=status.HTTP_200_OK)
                if post.visibility == "FRIENDS" and (Friend.objects.are_friends(user, post.author) or user.id == post.author.id):
                    return Response({"content": post.content}, status=status.HTTP_200_OK)
                if post.visibility == "FOAF" and (Friend.objects.are_foaf(user, post.author) or user.id == post.author.id):
                    return Response({"content": post.content}, status=status.HTTP_200_OK)
                if post.visibility == "SERVERONLY" and user.host in settings.FORMATTED_HOST_NAME:
                    return Response({"content": post.content}, status=status.HTTP_200_OK)
            return Response({"content": placeholder}, status=status.HTTP_200_OK)
        else:
            # We gotta pull it from somewhere else
            # We have the link, so we just have to request it.
            try:
                node = Node.objects.get(
                    hostname=post_link.split('posts/')[0])
                response = requests.get(post_link, auth=(
                    node.node_auth_username, node.node_auth_password), headers={
                    'content-type': 'appliation/json', 'Accept': 'application/json'}, timeout=GLOBAL_TIMEOUT)
                if response.status_code == 200:
                    post_json = response.json()
                    if 'post' not in post_json.keys():
                        # If 'post' is not in there, then the data is likely sent without being wrapped
                        post_json['post'] = post_json
                    if 'posts' in post_json.keys():
                        # For some reason, they can return an empty list here
                        if len(post_json["posts"]) == 0:
                            return Response({"content": placeholder}, status=status.HTTP_200_OK)
                        post_json["post"] = post_json["posts"][0]
                        del post_json["posts"]
                    post_data = post_json['post']
                    if type(post_data) == type(['foo']):
                        post_data = post_data[0]
                    # We have to sanitize the post, and the author of the post
                    post_data["author"] = sanitize_author(post_data["author"])
                    post_data = transformSource(post_data)
                    post = sanitize_post(post_data)
                    # # We should also be saving this post, so we can do this faster next time.
                    # post_serializer = PostSerializer(data=post)
                    # if post_serializer.is_valid():
                    #     try:
                    #         post_serializer.save()
                    #     except Exception as e:
                    #         print("Could not cache image", e)
                    # And now we have to check to see if we can actually see this post
                    if post["visibility"] == "PUBLIC":
                        return Response({"content": post["content"]}, status=status.HTTP_200_OK)
                    if post["visibility"] == "PRIVATE" and user.id in post["visibleTo"]:
                        return Response({"content": post["content"]}, status=status.HTTP_200_OK)
                    # Friends and FOAF visibility is trickier
                    if post["visibility"] == "FRIENDS":
                        if len(Author.objects.filter(id=post["author"]["id"])) == 1:
                            # We have them in our database
                            if Friend.objects.are_friends(Author.objects.get(id=post["author"]["id"]), user):
                                return Response({"content": post["content"]}, status=status.HTTP_200_OK)
                        return Response({"content": post["content"]}, status=status.HTTP_200_OK)
                    if post["visibility"] == "FOAF":
                        # We gotta actually query the other server to see if we can see this
                        try:
                            friends_response = requests.get(post["author"]["id"] + '/friends', auth=(
                                node.node_auth_username, node.node_auth_password), headers={'content-type': 'appliation/json', 'Accept': 'application/json'}, timeout=GLOBAL_TIMEOUT)
                            if friends_response.status_code == 200:
                                response_json = friends_response.json()
                                for author in response_json["authors"]:
                                    # A bunch of IDs
                                    if len(Author.objects.filter(id=author)) == 1:
                                        if Friend.objects.are_friends(user, Author.objects.get(id=author)):
                                            return Response({"content": post["content"]}, status=status.HTTP_200_OK)
                        except Timeout:
                            pass
                        return Response({"content": placeholder}, status=status.HTTP_200_OK)
                    else:
                        return Response({"content": placeholder}, status=status.HTTP_200_OK)
                else:
                    return Response({"content": placeholder}, status=status.HTTP_200_OK)
            except:
                return Response({"content": placeholder}, status=status.HTTP_200_OK)

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
                if len(Node.objects.filter(hostname__contains=comment["author"]["host"])) != 1:
                    return Response({
                        "query": "addComment",
                        "success": False,
                        "message": "This node is not authorized to post comments on this server."
                    }, status=status.HTTP_403_FORBIDDEN)
                elif (len(Author.objects.filter(id=comment["author"]["id"])) == 0):
                    # Node is authorized but author does not exit yet

                    # Change the displayName
                    node = list(Node.objects.filter(
                        hostname__contains=comment["author"]["host"]))[0]
                    comment["author"]['displayName'] = comment["author"]['displayName'] + \
                        " (" + node.server_username + ")"

                    # Change URL
                    author_parts = comment["author"]['id'].split('/')
                    authorID = author_parts[-1]
                    if authorID == '':
                        authorID = author_parts[-2]
                    # Our author URLS need a UUID, so we have to check if it's not
                    # The author's ID should never change!
                    try:
                        uuid.UUID(authorID)
                        comment["author"]['url'] = settings.FORMATTED_HOST_NAME + \
                            'author/' + authorID
                    except:
                        # We need to create a new one for the URL
                        if len(Author.objects.filter(id=comment["author"]["id"])) == 1:
                            # We already made one for them
                            comment["author"]['url'] = Author.objects.get(
                                id=comment["author"]["id"]).url
                        else:
                            # Give them a new one.
                            comment["author"]['url'] = settings.FORMATTED_HOST_NAME + \
                                'author/' + str(uuid.uuid4().hex)

                    # Serialize and save
                    author_serializer = AuthorSerializer(
                        data=comment["author"])
                    if (author_serializer.is_valid()):
                        try:
                            print('author saved')
                            author_serializer.save()
                        except Exception as e:
                            print(e)
                    else:
                        print(author_serializer.errors)
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
                    # Foaf is trickier.
                    for post in Post.objects.filter(visibility="FOAF"):
                        # If the author is friends with the author of the post, we can send it.
                        # If the author is friends with a friend of the author of the post, we can send it.
                        if Friend.objects.are_friends(post.author, author):
                            foaf_posts = foaf_posts | Post.objects.filter(
                                id=post.id)
                        else:
                            # We have to query the server to see who their friends are.
                            try:
                                node = Node.objects.get(
                                    server_username=request.user.displayName)
                                url = node.api_url + 'author/' + \
                                    author.id.split('author/')[-1] + '/friends'
                                response = requests.get(url, auth=(node.node_auth_username, node.node_auth_password), headers={
                                    'content-type': 'application/json', 'Accept': 'application/json'}, timeout=GLOBAL_TIMEOUT)
                                if response.status_code == 200:
                                    response_data = response.json()
                                    for friend_id in response_data["authors"]:
                                        # If they are friends with our author, they should be stored locally
                                        if len(Author.objects.filter(id=friend_id)) == 1:
                                            friend = Author.objects.get(
                                                id=friend_id)
                                            if Friend.objects.are_friends(friend, get_object_or_404(Author, id=post.author.id)):
                                                # They are FOAF. So we can send it.
                                                foaf_posts = foaf_posts | Post.objects.filter(
                                                    id=post.id)

                            except Exception:
                                # We can't reach the other server, so we can't in good conscience send this post.
                                pass

                post_query_set = public_posts | privated_posts | friend_posts | foaf_posts
        else:
            # They are not logged in and authenticated. So
            post_query_set = Post.objects.filter(
                visibility="PUBLIC", origin__contains=settings.FORMATTED_HOST_NAME)
        response = {'query': "posts"}
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
                    # Foaf is trickier.
                    for post in Post.objects.filter(visibility="FOAF", author=author_id):
                        # If the author is friends with the author of the post, we can send it.
                        # If the author is friends with a friend of the author of the post, we can send it.
                        if Friend.objects.are_friends(post.author, author):
                            foaf_posts = foaf_posts | Post.objects.filter(
                                id=post.id)
                        else:
                            # We have to query the server to see who their friends are.
                            try:
                                node = Node.objects.get(
                                    server_username=request.user.displayName)
                                url = node.api_url + 'author/' + \
                                    author.id.split('author/')[-1] + '/friends'
                                response = requests.get(url, auth=(node.node_auth_username, node.node_auth_password), headers={
                                    'content-type': 'application/json', 'Accept': 'application/json'}, timeout=GLOBAL_TIMEOUT)
                                if response.status_code == 200:
                                    response_data = response.json()
                                    for friend_id in response_data["authors"]:
                                        # If they are friends with our author, they should be stored locally
                                        if len(Author.objects.filter(id=friend_id)) == 1:
                                            friend = Author.objects.get(
                                                id=friend_id)
                                            if Friend.objects.are_friends(friend, get_object_or_404(Author, id=post.author.id)):
                                                # They are FOAF. So we can send it.
                                                foaf_posts = foaf_posts | Post.objects.filter(
                                                    id=post.id)

                            except Exception:
                                # We can't reach the other server, so we can't in good conscience send this post.
                                pass
                post_query_set = author_public_posts | author_private_posts | friend_posts | foaf_posts

        else:
            post_query_set = Post.objects.filter(
                author=author_id, visibility="PUBLIC")
        response = {"query": "posts"}
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
        response = {"query": "friends"}
        author1 = get_object_or_404(Author, id__icontains=pk)
        # We assume that the first author is in our DB.
        # But also, if they are friends, they should BOTH be in our DB.
        # So, we should not send a 404, but rather, if we cannot find the other user, we should return false.

        author2_results = Author.objects.filter(id__icontains=author2_id)
        if len(author2_results) == 0:
            # Return false
            response["authors"] = [author1.id, 'http://' + author2_id]
            response["friends"] = False
            return Response(response, status=status.HTTP_200_OK)
        # Otherwise, we have it
        author2 = Author.objects.get(id__icontains=author2_id)
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
                        # We have a lot of stuff regarding hostname matching that is causing issues. So let's just fix this once and for all.
                        valid_host_match = False
                        if request.data["author"]["host"][-1] == '/':
                            # it has a backslash, we can directly compare against the user's host.
                            if request.data["author"]["host"].split('://')[-1] == request.user.host.split('://')[-1] or request.data["author"]["host"] == request.user.host.split('://')[-1]:
                                valid_host_match = True
                        else:
                            # No trailing backslash
                            if request.data["author"]["host"].split('://')[-1] == request.user.host.split('://')[-1][:-1] or request.data["author"]["host"] == request.user.host.split('://')[-1][:-1]:
                                valid_host_match = True
                        if request.data["author"]["host"] != settings.FORMATTED_HOST_NAME and valid_host_match:
                            author = request.data["author"]
                            # We have to adjust a couple of things before we add them to our database
                            # First, they are a node, and need that node info
                            node = Node.objects.get(hostname=request.user.host)
                            author['host'] = node.hostname
                            # If the author id has no protocol, then we should be adding one.
                            # This would not be an issue if Team 4 included protocol in their IDs, but they don't seem to want to do that.
                            if 'http' not in author["id"]:
                                author["id"] = 'https://' + author["id"]
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
                            # If we have seen them before, we need to update them
                            if len(Author.objects.filter(id=author["id"])) == 1:
                                author_serializer = AuthorSerializer(
                                    Author.objects.get(id=author["id"]), data=author)
                            else:
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
        authors = Author.objects.filter(
            is_node=False, is_staff=False, host=settings.FORMATTED_HOST_NAME)
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
        response = author_dict
        return Response(response, status=status.HTTP_200_OK)
