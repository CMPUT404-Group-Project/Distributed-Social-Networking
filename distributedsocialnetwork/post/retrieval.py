from node.models import Node
from .models import Post, Comment
from author.models import Author
from post.serializers import PostSerializer, CommentSerializer
from author.serializers import AuthorSerializer
import requests
import datetime

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

                    author = sanitize_author(post["author"])
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
