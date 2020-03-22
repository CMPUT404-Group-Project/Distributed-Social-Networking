from node.models import Node
from .models import Post, Comment
from author.models import Author
from post.serializers import PostSerializer, CommentSerializer
from author.serializers import AuthorSerializer
import requests

# The purpose of this is to provide functions that can import Posts from the other Nodes.
# Each Node may not be completely to spec, so we may have to add server-specific compatibility here and there.


def sanitize_author(obj):
    # Given an author object, makes any modifications necessary to fit the spec and work with the serializer.

    # Mandala sanitizers
    if "display_name" in obj.keys():
        obj["displayName"] = obj["display_name"]
        del obj["display_name"]

    # Polar Bear sanitizers
    if "github" in obj.keys():
        if obj["github"] is None:
            obj["github"] = ""
    return obj


def sanitize_post(obj):
    # First thing we do is set the author to just the id of the author. this makes it deserializable
    obj["author"] = obj["author"]["id"]

    # Polar Bear sanitizers
    if "description" in obj.keys():
        if obj["description"] is None:
            obj["description"] = "t"

    return obj


def get_public_posts():
    # Returns a QuerySet of all the public posts retrieved from http://service/posts
    print("running")
    nodes = list(Node.objects.all())
    for node in nodes:
        if node.node_auth_username != "":
            # We have a set username and password to authenticate with this node.
            # We send a GET request to their endpoint.
            url = node.api_url + 'posts'
            response = requests.get('https://cmput404w20t06.herokuapp.com/api/posts', auth=(
                node.node_auth_username, node.node_auth_password), headers={'content-type': 'application/json', 'Accept': 'application/json'})
            if response.status_code == 200:
                # We have the geen light to continue. Otherwise, we just use what we have cached.
                posts_json = response.json()
                for post in posts_json["posts"]:
                    # We first have to ensure the author of each post is in our database.

                    author = sanitize_author(post["author"])
                    author_serializer = AuthorSerializer(data=author)

                    if author_serializer.is_valid():
                        author_serializer.save()
                    # We now have the author saved, so we can move on to the posts
                    post = sanitize_post(post)
                    post_serializer = PostSerializer(data=post)
                    if post_serializer.is_valid():
                        post_serializer.save()
                    else:
                        print(post_serializer.errors)
                        print("*****")
                        print(post)
                        print("=======")
