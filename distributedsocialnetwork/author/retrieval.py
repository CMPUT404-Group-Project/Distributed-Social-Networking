# Serializer for Author
import requests
from node.models import Node
from author.serializers import AuthorSerializer
from post.retrieval import sanitize_author
import datetime
import uuid
from django.conf import settings
from .models import Author
from django.shortcuts import get_object_or_404
from author.models import Author

def get_detailed_author(author_id):
    local_copy = get_object_or_404(Author, id__icontains=author_id)
    if (local_copy.origin != local_copy.source):
        local_split = local_copy.origin.split('/')
        node = Node.objects.get(hostname__contains=local_split[2])
        url = node.api_url + 'author/' + local_split[-1]
        response = requests.get(url, auth=(
            node.node_auth_username, node.node_auth_password), headers={
            'content-type': 'appliation/json', 'Accept': 'application/json'})
        if reponse.status_code == 200:
            author_json = response.json()
        author_data = author_json['author']
        author_data = transformSource(author_data)
        author = sanitize_author(author_data)
        author_serializer = AuthorSerializer(local_copy,data=author)
        if author_serializer.is_valid():
            print("it is valid")
            try:
                author_serializer.save()
                print("Updated author", author_serializer.validated_data["displayName"])
                new_copy = get_object_or_404(Author, id=author_serializer.validated_data["id"])
            except Exception as e:
                print("Error saving author", author_serializer.validated_data["displayName"], str(e))
        else:
            print("Error encountered:", author_serializer.errors)
            return local_copy
        return new_copy
    else:
        return local_copy


def transformSource(author_obj):
    del author_obj["source"]
    author_obj["source"] = settings.FORMATTED_HOST_NAME + 'author/' + author_obj['id']
    return author_obj






