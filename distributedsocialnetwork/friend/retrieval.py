from .models import Author
from node.models import Node
from friend.models import Friend, Follower
from author.serializers import AuthorSerializer
from post.retrieval import sanitize_author
from author.retrieval import get_detailed_author
import requests


def send_friend_request(author_id, friend_id):
    # Author is the one sending, friend is the one being sent to
    # Sends a friend request to the desired host based on the ids
    # Returns the response given
    author = Author.objects.get(id=author_id)
    # We now have the friend in the database
    friend = Author.objects.get(id=friend_id)
    # We format the following query:
    author_serializer = AuthorSerializer(friend)
    friend_data = dict(author_serializer.data)
    author_serializer = AuthorSerializer(author)
    author_data = dict(author_serializer.data)
    query = {
        "query": "friendrequest",
        "author": author_data,
        "friend": friend_data,
    }
    # Now we send it. But to what URL?
    node = Node.objects.get(hostname=friend.host)
    url = node.api_url + 'friendrequest'
    # And we send it off
    response = requests.post(url, json=query, auth=(node.node_auth_username, node.node_auth_password), headers={
                             'content-type': 'application/json', 'Accept': 'application/json'})
    return response


def get_friends_list(author_id):
    # Sends a request to retrieve the list of friends of a user, and returns a list of their IDs.
    # If we have the author we are querying in our db, we should be updating their friends list by doing this.
    # We will add the friends that we have PREVIOUSLY seen. This prevents us from sending requests out to other servers who we do not have
    # returns the response given

    author = Author.objects.get(id=author_id)
    author_uuid = author.id.split('author/')[1]
    print(author.host)
    if author.host[-1] != '/':
        host = author.host + '/'
    else:
        host = author.host
    # We get the node associated with that author
    node = Node.objects.get(hostname=host)
    url = node.api_url + 'author/' + author_uuid + '/friends'
    # And so we send the request
    response = requests.get(url, auth=(node.node_auth_username, node.node_auth_password), headers={
                            'content-type': 'application/json', 'Accept': 'application/json'})
    print(response.status_code)
    if response.status_code == 200:
        friends_response = response.json()
        if "authors" in friends_response:
            # We do the following for each author:
            # - If they are not from a host we are connected to, we are not going to do anything with it.
            # - If they are from a host we are connected to, and we have them saved in the database, we save the friendship.
            # - If they are from a host we are connected to but have not seen before, we save them in the database, and we save the friendship.
            for friend_id in friends_response["authors"]:
                friend_host = author_id.split('author/')[0]
                print(friend_host)
                if len(Node.objects.filter(hostname=host)) == 1:
                    stored = True
                    # We have talked to these people before, so let's do some work
                    if len(Author.objects.filter(id=friend_id)) != 1:
                        # We must add them first
                        stored = False
                        try:
                            # We have to get them from the other server
                            friend_uuid = friend_id.split('author/')[1]
                            node = Node.objects.get(hostname=friend_host)
                            url = node.api_url + 'author/' + friend_uuid
                            response = requests.get(url, auth=(
                                node.node_auth_username, node.node_auth_password), headers={
                                'content-type': 'appliation/json', 'Accept': 'application/json'})
                            if response.status_code == 200:
                                print(response.json())
                                if "author" in response.json().keys():
                                    # One minor modification to the displayName:
                                    author_data = sanitize_author(
                                        response.json()["author"])
                                    try:
                                        author_serializer = AuthorSerializer(
                                            data=author_data)
                                        if author_serializer.is_valid():
                                            author_serializer.save()
                                            print("We did it")
                                            stored = True
                                        else:
                                            print(author_serializer.errors)
                                    except Exception as e:
                                        print("Could not add author", e)
                            else:
                                print("failure")
                        except Exception as e:
                            print(e)
                    if stored:
                        # We aren't updating them, just adding reference to how they are friends
                        friend = Author.objects.get(id=friend_id)
                        Friend.objects.add_friend(author, friend)
