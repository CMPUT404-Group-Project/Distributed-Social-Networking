from django.contrib import admin
from .models import Node
from author.models import Author
import random
import string
# Register your models here.


class NodeAdmin(admin.ModelAdmin):
    # Our Node form in the admin panel
    model = Node
    list_display = ["server_username",
                    "server_password", "hostname", "api_url", "node_auth_username", "node_auth_password"]
    readonly_fields = ['auth_user']
    fields = [('auth_user'), ("server_username"),
              ("server_password"), ("hostname"), ("api_url"), ("node_auth_username"), ("node_auth_password")]

    def save_model(self, request, obj, form, change):
        # We need to create a new Author object and such
        displayName = obj.server_username
        password = obj.server_password
        hostname = obj.hostname
        # Email has to be unique. So we generate a new email.
        email = ''.join(random.choice(string.ascii_lowercase)
                        for i in range(10)) + "@node.com"
        if len(Author.objects.filter(displayName=displayName)) == 1:
            # User exists, we are updating our node
            new_author = Author.objects.get(displayName=displayName)
        else:
            new_author = Author.objects.create_user(
                displayName=displayName, password=password, first_name="NODE", last_name="NODE", email=email)
        new_author.host = hostname
        new_author.is_node = True
        new_author.is_active = True
        new_author.save()
        obj.auth_user = new_author
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        # We just delete the Author object we are attatched to
        # It will cascade
        node_user = Author.objects.get(displayName=obj.server_username)
        node_user.delete()
        # We want to delete all authors that belong to this host on deletion, which will cascade anything else they have touched.
        authors = Author.objects.filter(host__contains=obj.hostname)
        for author in authors:
            author.delete()
        # And sometimes the hostname on an author has no backslash:
        print(obj.hostname[:-1])
        authors = Author.objects.filter(host=obj.hostname[:-1])
        for author in authors:
            author.delete()
        super().delete_model(request, obj)


admin.site.register(Node, NodeAdmin)
