from .models import Author
from node.models import Node
from friend.models import Friend, Follower
from author.serializers import AuthorSerializer
import requests


def send_friend_request(author_id, friend_id):
    # Author is the one sending, friend is the one being sent to
    # Sends a friend request to the desired host based on the ids
    # Returns the response given
    print(author_id)
    author = Author.objects.get(id=author_id)
    if len(Author.objects.filter(id=friend_id)) == 0:
        # We don't have this author in our database, so we need to
        # save it in the database first
        # TODO: Send a proper request to get Author details, and serialize them
        #       once we have the method to retrieve the author's details
        Author.objects.create(displayName="unknown", id=friend_id,
                              url=friend_id, host=friend_id.split('author/')[0])
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
    print(response.status_code, response.json())
    return response
