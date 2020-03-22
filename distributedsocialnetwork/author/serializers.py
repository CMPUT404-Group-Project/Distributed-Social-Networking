# Serializer for Author

from rest_framework.serializers import ModelSerializer
from rest_framework import serializers, fields


from .models import Author


class AuthorSerializer(ModelSerializer):
    id = serializers.CharField(max_length=100)
    host = serializers.CharField(max_length=100)
    url = serializers.CharField(max_length=100)

    class Meta:
        model = Author
        fields = [
            'id', 'host', 'displayName', 'url', 'github'
        ]
