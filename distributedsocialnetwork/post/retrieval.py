import requests
from node.models import Node
from post.serializers import PostSerializer
from author.serializers import AuthorSerializer
import requests
import datetime
from django.conf import settings
from .models import Post
from django.shortcuts import get_object_or_404


# The purpose of this is to provide functions that can import Posts from the other Nodes.
# Each Node may not be completely to spec, so we may have to add server-specific compatibility here and there.


def sanitize_author(obj):
    # Given an author object, makes any modifications necessary to fit the spec and work with the serializer.

    # Mandala sanitizers
    if "display_name" in obj.keys():
        obj["displayName"] = obj["display_name"]
        del obj["display_name"]

    return obj


def sanitize_post(obj):
    # First thing we do is set the author to just the id of the author. this makes it deserializable
    obj["author"] = obj["author"]["id"]

    obj["visibleTo"] = ','.join(obj["visibleTo"])
    obj["categories"] = ','.join(obj["visibleTo"])
    return obj


def get_public_posts():
    # Returns a QuerySet of all the public posts retrieved from http://service/posts
    print("running")
    nodes = list(Node.objects.all())
    public_posts = Post.objects.none()
    for node in nodes:
        if node.node_auth_username != "":
            # We have a set username and password to authenticate with this node.
            # We send a GET request to their endpoint.
            url = node.api_url + 'posts'
            # response = requests.get(
            #     url, auth=(
            #         node.node_auth_username, node.node_auth_password), headers={'content-type': 'application/json', 'Accept': 'application/json'})
            response = requests.get(
                url, headers={'content-type': 'application/json', 'Accept': 'application/json'})
            if response.status_code == 200:
                # We have the geen light to continue. Otherwise, we just use what we have cached.
                posts_json = response.json()
                for post in posts_json["posts"]:
                    # We first have to ensure the author of each post is in our database.
                    post = transformSource(post)
                    author = sanitize_author(post["author"])
                    author['displayName'] = author['displayName'] + \
                        " (" + node.server_username + ")"
                    author_parts = author['id'].split('/')
                    authorID = author_parts[-1]
                    if authorID == '':
                        authorID = author_parts[-2]
                    author['url'] = settings.FORMATTED_HOST_NAME + \
                        'author/' + authorID
                    author_serializer = AuthorSerializer(data=author)
                    if author_serializer.is_valid():
                        try:
                            author_serializer.save()
                            # We now have the author saved, so we can move on to the posts
                            post = sanitize_post(post)
                            post_serializer = PostSerializer(data=post)
                            if post_serializer.is_valid():
                                try:
                                    post_serializer.save()
                                    print("Loaded post",
                                          post_serializer.validated_data["title"])
                                    public_posts = public_posts | Post.objects.filter(
                                        id=post_serializer.validated_data["id"])

                                except Exception as e:
                                    print("Error saving post",
                                          post_serializer.validated_data["title"], str(e))
                            else:
                                print("Error encountered:",
                                      post_serializer.errors)
                        except Exception as e:
                            print(e)
    return public_posts


def get_detailed_post(post_id):
    # Assumes that the post is already in our DB due to the fact that you are passing an ID.
    local_copy = get_object_or_404(Post, id=post_id)
    if(local_copy.origin != local_copy.source):
        local_split = local_copy.origin.split('/')
        node = Node.objects.get(hostname__contains=local_split[2])
        url = node.api_url + 'posts/' + local_split[-1]
        response = requests.get(
            url, auth=(
                node.node_auth_username, node.node_auth_password), headers={'content-type': 'application/json', 'Accept': 'application/json'})
        if response.status_code == 200:
            post_json = response.json()
        post_data = post_json['posts'][0]
        post_data = transformSource(post_data)
        post = sanitize_post(post_data)
        post_serializer = PostSerializer(local_copy, data=post)
        if post_serializer.is_valid():
            try:
                post_serializer.save()
                print("Updated post",
                      post_serializer.validated_data["title"])
                new_copy = get_object_or_404(
                    Post, id=post_serializer.validated_data["id"])
                # new_copy = Post.objects.filter(
                #     id=)

            except Exception as e:
                print("Error saving post",
                      post_serializer.validated_data["title"], str(e))
        else:
            print("Error encountered:",
                  post_serializer.errors)

        # new_copy = local_copy  # FOR NOW
        return new_copy
    else:
        return local_copy
    # url =
    # response = requests.get(
    #             url, headers={'content-type': 'application/json', 'Accept': 'application/json'})


def transformSource(post_obj):
    del post_obj["source"]
    post_obj["source"] = settings.FORMATTED_HOST_NAME + \
        'posts/' + post_obj['id']
    return post_obj
