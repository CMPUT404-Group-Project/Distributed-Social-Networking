from .models import Author
from node.models import Node
from friend.models import Friend, Follower
from .serializers import AuthorSerializer
import requests

# These are functions to import Authors from other Nodes.


def get_friends_list(author_id):
    # Given a foreign author id, sends a request to that author's friends list
    # We have to parse the author's id to know where to send them
    if author_id[-1] == '/':
        # If there is a backslash at the end of the id, remove it
        author_id = author_id[:-1]
    # We split up the author_id to get the host
    host = author_id.split('author')[0]
    uuid = author_id.split('/')[-1]
    print(author_id)
    # We get the node for that host, assuming we have it set up.
    if len(Node.objects.filter(hostname=host)) == 1:
        node = Node.objects.get(hostname=host)
        # The URI of the request is built from their API url
        author_api_url = node.api_url + '/author/' + uuid
        response = requests.get(author_api_url, auth=(node.node_auth_username, node.node_auth_password), headers={
                                'content-type': 'application/json', 'Accept': 'application/json'})
        if response.status_code == 200:
            friends_json = response.json()
            print(friends_json)
        else:
            print(response)
