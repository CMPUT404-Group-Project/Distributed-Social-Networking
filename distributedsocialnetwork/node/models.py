from django.db import models
from author.models import Author
# Create your models here.


class NodeManager(models.Manager):
    def create(self, **obj_data):
        # We create a new Author/User object with which to map to the Author database
        username = obj_data["server_username"]
        password = obj_data["server_password"]
        hostname = obj_data["hostname"]
        new_author = Author.objects.create_user(
            displayName=username, password=password, first_name="NODE", last_name="NODE", email="node@node.com")
        # We manually set some aspects of new_author
        new_author.host = hostname
        new_author.is_node = True
        new_author.is_active = True
        new_author.save()
        # And now we set the auth_user field to this new author
        obj_data["auth_user"] = new_author
        return super().create(**obj_data)

    def remove(self, node):
        # To delete a node object and also delete its corresponding author object
        Author.objects.get(displayName=node.server_username).delete()


class Node(models.Model):
    # auth_user is an Author object because this is the model configured to use Basic Auth.
    auth_user = models.ForeignKey(Author, on_delete=models.CASCADE)
    hostname = models.URLField()  # The url where the service is located
    api_url = models.URLField()  # The url for their REST API
    server_username = models.CharField(max_length=100)
    server_password = models.CharField(max_length=100)

    objects = NodeManager()
