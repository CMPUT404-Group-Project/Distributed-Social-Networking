import requests
from requests.exceptions import Timeout
from node.models import Node
from post.serializers import PostSerializer, CommentSerializer
from author.serializers import AuthorSerializer
import requests
import datetime
import uuid
from django.conf import settings
from .models import Post, Comment
from django.shortcuts import get_object_or_404
from author.models import Author


# The purpose of this is to provide functions that can import Posts from the other Nodes.
# Each Node may not be completely to spec, so we may have to add server-specific compatibility here and there.
GLOBAL_TIMEOUT = 10


def sanitize_author(obj):
    # Given an author object, makes any modifications necessary to fit the spec and work with the serializer.

    # Mandala sanitizers
    if "display_name" in obj.keys():
        obj["displayName"] = obj["display_name"]
        del obj["display_name"]
    if "id" in obj.keys():
        # They sometimes give us just the UUID. They should not do that.
        if '/author/' not in obj["id"]:
            # We gotta change it
            if "host" in obj.keys():
                if obj["host"] is not None:
                    # If they don't have a host, we have bigger issues
                    obj["id"] = obj["host"] + '/author/' + \
                        obj["id"].replace('-', "")
        # They sometimes give us it without a protocol.
        if obj["id"][:4] != "http":
            obj["id"] = 'https://' + obj['id']
    if "host" in obj.keys():
        if obj["host"] is not None:
            if obj["host"][:4] != 'http':
                obj["host"] = 'https://' + obj["host"]
    if "url" in obj.keys():
        if obj["url"][:4] != 'http':
            obj["url"] = 'https://' + obj["url"]
    if "github" in obj.keys():
        if obj["github"] is None:
            obj["github"] = ""
    if "first_name" in obj.keys():
        obj["firstName"] = obj["first_name"]
        del obj["first_name"]
    if "last_name" in obj.keys():
        obj["lastName"] = obj["last_name"]
        del obj["last_name"]

    return obj


def sanitize_post(obj):
    # First thing we do is set the author to just the id of the author. this makes it deserializable
    obj["author"] = obj["author"]["id"]

    if "contentType" in obj.keys():
        if obj["contentType"] == "TYPE_MARKDOWN":
            obj["contentType"] = "text/markdown"
        elif obj["contentType"] == "TYPE_PLAIN":
            obj["contentType"] = "text/plain"

    if "id" in obj.keys():
        CommentSerializer
        if type(obj["id"]) == type(1):
            # We have to give it a unique UUID.
            # We will give it one, but only if we have not seen it before
            if len(Post.objects.filter(origin=obj["origin"])) == 0:
                obj["id"] = str(uuid.uuid4().hex)
            else:
                obj["id"] = str(Post.objects.get(origin=obj["origin"]).id)
        # We have to convert to a uuid
        obj["id"] = str(uuid.UUID(obj["id"]))

    if "description" in obj.keys():
        if obj["description"] is None:
            obj["description"] = ""

    if "visibleTo" in obj.keys():
        if obj["visibleTo"] is None:
            obj["visibleTo"] = []

    if "published" in obj.keys():
        try:
            obj["published"] = datetime.datetime.strptime(
                obj["published"], "%Y-%m-%d").strftime('%Y-%m-%dT%H:%M:%S%z')
        except:
            pass
    obj["visibleTo"] = ','.join(obj["visibleTo"])
    obj["categories"] = ','.join(obj["visibleTo"])

    return obj


def sanitize_comment(obj):
    if 'content' in obj.keys():
        obj['comment'] = obj['content']
    if 'author' in obj.keys():
        obj['author'] = sanitize_author(obj['author'])
    if 'contentType' in obj.keys():
        if obj['contentType'] == "":
            # Why is this blank? Whatever, treat it as plaintext
            obj['contentType'] = 'text/plain'
    if "published" in obj.keys():
        try:
            obj["published"] = datetime.datetime.strptime(
                obj["published"], "%Y-%m-%d").strftime('%Y-%m-%dT%H:%M:%S%z')
        except:
            pass
    return obj


def transformSource(post_obj):
    del post_obj["source"]
    post_obj["source"] = settings.FORMATTED_HOST_NAME + \
        'posts/' + post_obj['id']
    return post_obj


def get_public_posts():
    # Returns a QuerySet of all the public posts retrieved from http://service/posts
    # print("running")
    nodes = list(Node.objects.all())
    public_posts = Post.objects.none()
    for node in nodes:
        if node.node_auth_username != "":
            # We have a set username and password to authenticate with this node.
            # We send a GET request to their endpoint.
            url = node.api_url + 'posts'
            # print("sending to ", url)
            # response = requests.get(
            #     url, auth=(
            #         node.node_auth_username, node.node_auth_password), headers={'content-type': 'application/json', 'Accept': 'application/json'})
            response = requests.get(
                url, auth=(node.node_auth_username, node.node_auth_password), headers={'content-type': 'application/json', 'Accept': 'application/json'}, timeout=GLOBAL_TIMEOUT)
            if response.status_code == 200:
                # print(response.json())
                # We have the geen light to continue. Otherwise, we just use what we have cached.
                posts_json = response.json()
                for post in posts_json["posts"]:
                    # We first have to ensure the author of each post is in our database.
                    # We should not have these posts in our database if they are from a site we have no connection to.
                    hostname = post['origin'].split('posts/')[0]
                    if len(Node.objects.filter(hostname=hostname)) == 1:

                        author = sanitize_author(post["author"])
                        post = sanitize_post(post)
                        post = transformSource(post)
                        author['displayName'] = author['displayName'] + \
                            " (" + node.server_username + ")"
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
                        if (len(Author.objects.filter(id=author['id'])) == 1):
                            old_author = Author.objects.get(id=author['id'])
                            author_serializer = AuthorSerializer(
                                old_author, data=author)
                        else:
                            author_serializer = AuthorSerializer(data=author)
                        if author_serializer.is_valid():
                            try:
                                author_serializer.save()
                                # print("saved author",
                                #       author_serializer.validated_data["displayName"])
                                # We now have the author saved, so we can move on to the posts
                                if len(Post.objects.filter(origin=post["origin"])) == 1:
                                    post_serializer = PostSerializer(
                                        Post.objects.get(origin=post["origin"]), data=post)
                                else:
                                    post_serializer = PostSerializer(data=post)
                                if post_serializer.is_valid():
                                    try:
                                        post_serializer.save()
                                        # print("Loaded post",
                                        #       post_serializer.validated_data["title"])
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
                        else:
                            print("Error encountered:",
                                  author_serializer.errors)
                    else:
                        continue

    return public_posts


def get_detailed_post(post_id):
    # Assumes that the post is already in our DB due to the fact that you are passing an ID.
    local_copy = get_object_or_404(Post, id=post_id)
    if(local_copy.origin != local_copy.source):
        local_split = local_copy.origin.split('/')
        # Ignore github posts
        if local_split[2] == 'api.github.com':
            return local_copy
        node = Node.objects.get(hostname__contains=local_split[2])
        url = node.api_url + 'posts/' + local_split[-1]
        try:
            response = requests.get(
                url, auth=(
                    node.node_auth_username, node.node_auth_password), headers={'content-type': 'application/json', 'Accept': 'application/json'}, timeout=GLOBAL_TIMEOUT)
        except Timeout:
            print("Request to", url, "timed out")
            return None
        if response.status_code == 404:
            # The post is gone!
            Post.objects.get(id=post_id).delete()
            return None
        if response.status_code == 200:
            post_json = response.json()
            # TODO: Talk to Group 4 about how to consistently do the detailed post endpoint
            if 'post' not in post_json.keys():
                # If 'post' is not in there, then the data is likely sent without being wrapped
                post_json['post'] = post_json
            if 'posts' in post_json.keys():
                # We have to add an exception here if this list is empty. Group 4 is doing some weird stuff.
                if len(post_json["posts"]) == 0:
                    # We have no post to update from.
                    return local_copy
                post_json["post"] = post_json["posts"][0]
                del post_json["posts"]
            post_data = post_json['post']
            if type(post_data) == type(['foo']):
                post_data = post_data[0]
            # Let us sanitize the author
            post_data["author"] = sanitize_author(post_data["author"])
            post = sanitize_post(post_data)
            post_data = transformSource(post_data)

            post_serializer = PostSerializer(local_copy, data=post)
            if post_serializer.is_valid():
                # print("it is valid")
                try:
                    post_serializer.save()
                    # print("Updated post",
                    #       post_serializer.validated_data["title"])
                    new_copy = get_object_or_404(
                        Post, id=post_serializer.validated_data["id"])
                    return new_copy
                    # new_copy = Post.objects.filter(
                    #     id=)
                except Exception as e:
                    print("Error saving post",
                          post_serializer.validated_data["title"], str(e))
            else:
                print("Error encountered:",
                      post_serializer.errors)
                return local_copy
    # If it gets this far, return what is cached.
    return local_copy


def get_comments(pk):
    local_comments = Comment.objects.filter(post_id=pk)
    comm_ids = []
    for comment in local_comments:
        comm_ids.append(comment.id)
    local_copy = get_object_or_404(Post, id=pk)
    if(local_copy.origin != local_copy.source):
        local_split = local_copy.origin.split('/')
        # Ignore github posts
        if local_split[2] == 'api.github.com':
            return Comment.objects.filter(post_id=pk)
        node = Node.objects.get(hostname__contains=local_split[2])
        url = node.api_url + 'posts/' + local_split[-1] + '/comments'
        try:
            response = requests.get(url, auth=(node.node_auth_username, node.node_auth_password),
                                    headers={'content-type': 'application/json', 'Accept': 'application/json'}, timeout=GLOBAL_TIMEOUT)
        except Timeout:
            print("Request to", url, "timed out")
            return Comment.objects.filter(post_id=pk)
        if response.status_code == 200:
            comments_json = response.json()
            for comment in comments_json["comments"]:
                try:
                    comment = sanitize_comment(comment)
                    if len(Author.objects.filter(id=comment["author"]["id"])) != 1:
                        # We gotta store them, if they are from a host we can talk with.
                        if len(Node.objects.filter(hostname__icontains=comment["author"]["host"])) == 1:
                            try:
                                node = Node.objects.get(
                                    hostname__icontains=comment["author"]["host"])
                                comment["author"]["url"] = settings.FORMATTED_HOST_NAME + \
                                    'author/' + \
                                    comment["author"]["url"].split(
                                        '/author')[-1]
                                author['displayName'] = author['displayName'] + \
                                    " (" + node.server_username + ")"
                                author_serializer = AuthorSerializer(
                                    data=comment["author"])
                                if author_serializer.is_valid():
                                    author_serializer.save()
                            except:
                                # We can't save them, so print errors and continue.
                                print(author_serializer.errors)
                    # Otherwise, if we have them already stored, who cares. We won't update the author right now.
                    comment["author"] = comment["author"]["id"]
                    comment["post_id"] = pk
                    # But we have a dilemma now.
                    # Team 6 uses ints for their comment ids. Which means, when we pull in a comment, it will not have the correct id.
                    # Because of this, if we are not careful, we can create duplicate comments.
                    # So we have to try and find a match in our local database for the comment first, without relying on ID.
                    try:
                        uuid_version = uuid.UUID(comment["id"])
                    except:
                        # It is not a UUID, because it's an int.
                        if len(Comment.objects.filter(author=comment["author"], comment=comment["comment"], post_id=local_copy)) == 0:
                            # We don't have this comment stored. Let's get a new UUID for it.
                            comment["id"] = str(uuid.uuid4().hex)
                        else:
                            # We have it stored. We can update it as long as we use the same id as before.
                            comment["id"] = str(Comment.objects.filter(
                                author=comment["author"], comment=comment["comment"], post_id=local_copy)[0].id)
                    if uuid.UUID(comment["id"]) in comm_ids:
                        comment_serializer = CommentSerializer(
                            Comment.objects.get(id=comment["id"]), data=comment)
                        if comment_serializer.is_valid():
                            comment_serializer.save()
                    else:
                        comment_serializer = CommentSerializer(data=comment)
                        try:
                            if comment_serializer.is_valid(raise_exception=True):
                                comment_serializer.save()
                            else:
                                print(comment_serializer.errors)
                        except Exception as e:
                            print(e)
                except Exception as e:
                    print("Error serializing comment:", comment["id"], str(e))
        else:
            print("Error GETting:", url)
    return Comment.objects.filter(post_id=pk)


def post_foreign_comment(new_comment):
    # Save post object
    post = new_comment.post_id

    # get author data
    author = Author.objects.get(id=new_comment.author_id)
    author_serializer = AuthorSerializer(author)
    author_data = dict(author_serializer.data)

    # Serialize and clean
    comment_serializer = CommentSerializer(new_comment)
    comment_data = dict(comment_serializer.data)
    del comment_data["post_id"]
    comment_data["author"] = author_data

    # build query
    query = {
        "query": "addComment",
        "post": post.origin,
        "comment": comment_data
    }
    # send POST request
    node = Node.objects.get(hostname__icontains=post.origin.split('/')[2])
    # url = node.api_url + 'posts/' + str(post.id) + '/' + 'comments'
    url = post.origin + '/comments'
    print("Sending comment to", url)
    try:
        response = requests.post(url, json=query, auth=(node.node_auth_username, node.node_auth_password), headers={
            'content-type': 'application/json', 'Accept': 'application/json'}, timeout=GLOBAL_TIMEOUT)
        if response.status_code == 500:
            # We should try again with a backslash
            print("sending comment to", url)
            try:
                url = url + '/'
                response = requests.post(url, json=query, auth=(node.node_auth_username, node.node_auth_password), headers={
                    'content-type': 'application/json', 'Accept': 'application/json'}, timeout=GLOBAL_TIMEOUT)
            except Exception as e:
                print(e)
                response = None
    except Exception as e:
        print("Sending comment to", url)
        # Failed.
        # Let us try again for the response, with a backslash
        try:
            url = url + '/'
            response = requests.post(url, json=query, auth=(node.node_auth_username, node.node_auth_password), headers={
                'content-type': 'application/json', 'Accept': 'application/json'}, timeout=GLOBAL_TIMEOUT)
        except Exception as e:
            print(e)
            response = None

    return response
