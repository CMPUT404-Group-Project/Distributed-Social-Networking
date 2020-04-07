from .models import Author
from node.models import Node
from friend.models import Friend, Follower
from author.serializers import AuthorSerializer
from post.retrieval import sanitize_author
from author.retrieval import get_detailed_author
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import requests
from requests.exceptions import Timeout

GLOBAL_TIMEOUT = 10


def send_friend_request(author_id, friend_id):
    # Author is the one sending, friend is the one being sent to
    # Sends a friend request to the desired host based on the ids
    # Returns the response given
    author = Author.objects.get(id=author_id)
    # We now have the friend in the database
    friend = Author.objects.get(id=friend_id)
    if len(Node.objects.filter(hostname__contains=friend.host)) != 1:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    node = Node.objects.get(hostname__contains=friend.host)
    # We format the following query:
    author_serializer = AuthorSerializer(friend)
    friend_data = dict(author_serializer.data)
    # We modified some of the friend's author data going in, so we have to fix it before it goes out.
    friend_data['url'] = friend_data['id']
    friend_data['displayName'] = friend_data["displayName"].split(
        (' (' + str(node.server_username) + ')'))[-2]
    author_serializer = AuthorSerializer(author)
    author_data = dict(author_serializer.data)
    query = {
        "query": "friendrequest",
        "author": author_data,
        "friend": friend_data,
    }

    # Now we send it. But to what URL?
    node = Node.objects.get(hostname__icontains=friend.host)
    url = node.api_url + 'friendrequest'
    # And we send it off
    try:
        response = requests.post(url, json=query, auth=(node.node_auth_username, node.node_auth_password), headers={
            'content-type': 'application/json', 'Accept': 'application/json'}, timeout=GLOBAL_TIMEOUT)
    except:
        # Let us try again for the response, with a backslash
        try:
            url = url + '/'
            response = requests.post(url, json=query, auth=(node.node_auth_username, node.node_auth_password), headers={
                'content-type': 'application/json', 'Accept': 'application/json'}, timeout=GLOBAL_TIMEOUT)
        except:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if response.status_code == 200 or response.status_code == 201:
        # If it succeeded, we should immediately pull their friends list to make sure it is updated
        update_friends_list(friend_id)
    return response


def update_friends_list(author_id):
    # Sends a request to retrieve the list of friends of a user, and returns a list of their IDs.
    # If we have the author we are querying in our db, we should be updating their friends list by doing this.
    # We will add the friends that we have PREVIOUSLY seen. This prevents us from sending requests out to other servers who we do not have
    # returns the response given

    author = Author.objects.get(id=author_id)
    # We should be sending to the original server
    # To get the url, we strip the id, replace with the api_url, and send that
    try:
        node = Node.objects.get(hostname=author.host)
    except:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    api_url = node.api_url
    url = api_url + 'author/' + author_id.split('author/')[-1]

    if url[-1] == '/':
        url += 'friends'
    else:
        url += '/friends'
    # And so we send the request
    try:
        response = requests.get(url, auth=(node.node_auth_username, node.node_auth_password), headers={
            'content-type': 'application/json', 'Accept': 'application/json'}, timeout=GLOBAL_TIMEOUT)
    except Timeout:
        print("timeout sending request to", url)
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    if response.status_code == 200 or response.status_code == 201:
        # First, lets get our current list of friends for this author.
        # If we have some in our list that are not in their list, we should remove it locally.
        current_friends = Friend.objects.get_friends(
            Author.objects.get(id=author_id))
        friend_ids = []
        for friend in list(current_friends):
            friend_ids.append(friend.id)
        friends_response = response.json()
        if "authors" in friends_response:
            # We do the following for each author:
            # - If they are not from a host we are connected to, we are not going to do anything with it.
            # - If they are from a host we are connected to, and we have them saved in the database, we save the friendship.
            # - If they are from a host we are connected to but have not seen before, we save them in the database, and we save the friendship.
            for friend_id in friends_response["authors"]:
                friend_host = author_id.split('author/')[0]
                if len(Node.objects.filter(hostname=friend_host)) == 1:
                    stored = True
                    # We have talked to these people before, so let's do some work
                    if len(Author.objects.filter(id=friend_id)) != 1:
                        # We must add them first
                        stored = False
                        if get_detailed_author(author_id=friend_id):
                            stored = True
                    if stored:
                        # We aren't updating them, just adding reference to how they are friends
                        friend = Author.objects.get(id=friend_id)
                        Friend.objects.add_friend(author, friend)
            # Finally, we check to see if they have fewer friends than before.
            for friend_id in list(set(friend_ids) - set(friends_response["authors"])):
                Friend.objects.remove_friend(Author.objects.get(id=author_id), Author.objects.get(
                    id=friend_id))
    return response
