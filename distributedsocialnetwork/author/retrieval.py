from node.models import Node
from .models import Author
from post.models import Post, Comment
from post.serializers import PostSerializer, CommentSerializer
from post.retrieval import sanitize_author, sanitize_post, transformSource
from friend.models import Friend
from author.serializers import AuthorSerializer
import requests
import datetime
import uuid
from django.conf import settings
from django.shortcuts import get_object_or_404

# Given a QuerySet 'posts', returns another QuerySet
# containing the posts that 'author_id' can see.


def filter_posts(posts, author_id):
    public_posts = posts.filter(visibility="PUBLIC")
    user_posts = posts.filter(author=author_id)
    privated_posts = posts.filter(
        visibility="PRIVATE", visibleTo__icontains=author_id)
    serveronly_posts = posts.filter(
        visibility="SERVERONLY", author__in=Friend.objects.get_friends(author_id))
    friend_posts = posts.filter(
        visibility="FRIENDS", author__in=Friend.objects.get_friends(author_id))
    foaf_posts = posts.filter(
        visibility="FOAF", author__in=Friend.objects.get_foaf(author_id))
    post_query_set = public_posts | user_posts | privated_posts | serveronly_posts | friend_posts | foaf_posts
    return post_query_set

# Returns a QuerySet of all foreign posts the specified author is authorized to see


def get_visible_posts(author_id):
    author = get_object_or_404(Author, id=author_id)
    nodes = list(Node.objects.all())
    visible_posts = Post.objects.none()
    for node in nodes:
        if node.node_auth_username != "":
            # We have a set username and password to authenticate with this node.
            # We send a GET request to their endpoint.
            url = node.api_url + 'author/posts'
            print("sending to ", url)
            # Include a header containing the Author's id, other nodes may not conform to this.
            response = requests.get(
                url, auth=(node.node_auth_username, node.node_auth_password), headers={'content-type': 'application/json', 'Accept': 'application/json', 'AuthorId': author.id})
            if response.status_code == 200:
                # print(response.json())
                # We have the geen light to continue. Otherwise, we just use what we have cached.
                posts_json = response.json()
                for post in posts_json["posts"]:
                    # We first have to ensure the author of each post is in our database.

                    author = sanitize_author(post["author"])
                    post = sanitize_post(post)
                    post = transformSource(post)
                    author['displayName'] = author['displayName'] + \
                        " (" + node.server_username + ")"
                    author_parts = author['id'].split('/')
                    authorID = author_parts[-1]
                    if authorID == '':
                        authorID = author_parts[-2]
                    author['url'] = settings.FORMATTED_HOST_NAME + \
                        'author/' + authorID
                    # Check if we already have that author in our db
                    # already. If so, update it.
                    if (len(Author.objects.filter(id=author['id'])) == 1):
                        old_author = Author.objects.get(id=author['id'])
                        author_serializer = AuthorSerializer(
                            old_author, data=author)
                    else:
                        author_serializer = AuthorSerializer(data=author)
                    if author_serializer.is_valid():
                        try:
                            author_serializer.save()
                            print("saved author")
                            # We now have the author saved, so we can move on to the posts

                            post_serializer = PostSerializer(data=post)
                            if post_serializer.is_valid():
                                try:
                                    post_serializer.save()
                                    print("Loaded post",
                                          post_serializer.validated_data["title"])
                                    visible_posts = visible_posts | Post.objects.filter(
                                        id=post_serializer.validated_data["id"])

                                except Exception as e:
                                    print("Error saving post",
                                          post_serializer.validated_data["title"], str(e))
                            else:
                                print("Error encountered:",
                                      post_serializer.errors)
                        except Exception as e:
                            print(e)
    # Filter returned posts to return only those this author can see
    return filter_posts(visible_posts, author_id)


def get_detailed_author(author_id):
    # We want to either store the author for the first time, or save them

    # local_copy = get_object_or_404(Author, id__icontains=author_id)
    if (settings.FORMATTED_HOST_NAME != author_id.split('author/')[0]):
        try:
            if len(Node.objects.filter(hostname=author_id.split('author/')[0])) != 1:
                # We don't have the credentials to get this user's info
                return None
            local_split = author_id.split('author/')
            node = Node.objects.get(hostname=local_split[0])
            url = node.api_url + 'author/' + local_split[-1]
            response = requests.get(url, auth=(
                node.node_auth_username, node.node_auth_password), headers={
                'content-type': 'appliation/json', 'Accept': 'application/json'})
            if response.status_code == 200:
                author_json = response.json()
            author_data = author_json['author']
            author = sanitize_author(author_data)
            # A couple of modifications so we can easily tell they are a foreign author
            author['displayName'] = author['displayName'] + \
                " (" + node.server_username + ")"
            author_parts = author['id'].split('/')
            authorID = author_parts[-1]
            if authorID == '':
                authorID = author_parts[-2]
            author['url'] = settings.FORMATTED_HOST_NAME + \
                'author/' + authorID
            if len(Author.objects.filter(id=author_id)) == 1:
                # We have an author already, we need to update it
                author_serializer = AuthorSerializer(
                    Author.objects.get(id=author_id), data=author)
            else:
                author_serializer = AuthorSerializer(data=author)
            if author_serializer.is_valid():
                try:
                    author_serializer.save()
                    print("Updated author",
                          author_serializer.validated_data["displayName"])
                    new_copy = get_object_or_404(
                        Author, id=author_serializer.validated_data["id"])
                except Exception as e:
                    print("Error saving author",
                          author_serializer.validated_data["displayName"], str(e))
            else:
                print("Error encountered:", author_serializer.errors)
                return None
            return new_copy
        except Exception as e:
            print("Error updating user:", e)
            return None
    else:
        # We have this user already, it belongs to our server
        return get_object_or_404(Author, id=author_id)


def transformSource(author_obj):
    del author_obj["source"]
    author_obj["source"] = settings.FORMATTED_HOST_NAME + \
        'author/' + author_obj['id']
    return author_obj
