from django.db import models
from author.models import Author
import random
import string
# Create your models here.


class NodeManager(models.Manager):
    def create(self, **obj_data):
        # We create a new Author/User object with which to map to the Author database
        username = obj_data["server_username"]
        password = obj_data["server_password"]
        hostname = obj_data["hostname"]
        # Email has to be unique. So we generate a new email.
        email = ''.join(random.choice(string.ascii_lowercase)
                        for i in range(10)) + "@node.com"
        new_author = Author.objects.create_user(
            displayName=username, password=password, first_name="NODE", last_name="NODE", email=email)
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
        Author.objects.get(host=node.hostname).delete()


class Node(models.Model):
    # auth_user is an Author object because this is the model configured to use Basic Auth.
    auth_user = models.ForeignKey(Author, on_delete=models.CASCADE)
    # The url where the service is located
    hostname = models.URLField(help_text="Ex: http://dsnfof.herokuapp.com/")
    # The url for their REST API
    api_url = models.URLField(help_text="Ex: http://dsnfof.herokuapp.com/api/")
    server_username = models.CharField(
        max_length=10, help_text="The username the foreign server uses to connect to us.")
    server_password = models.CharField(
        max_length=100, help_text="The password the foreign server uses to connect to us.")
    # These next two are OUR credentials for logging into this server.
    node_auth_username = models.CharField(
        max_length=100, default="", help_text="The username we use when connecting to the foreign server.")
    node_auth_password = models.CharField(
        max_length=100, default="", help_text="The password we use when connecting to the foreign server.")

    objects = NodeManager()
