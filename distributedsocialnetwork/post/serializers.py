# Serializers for Posts and Comments
from rest_framework import serializers

from .models import Post, Comment

from author.models import Author
from author.serializers import AuthorSerializer

from json import loads, dumps

from django.core.paginator import Paginator
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CommentSerializer(serializers.ModelSerializer):
    # Serializes a comment in the way the API specifies.
    author = AuthorSerializer()

    class Meta:
        model = Comment
        fields = ['author', 'comment', 'contentType', 'published', 'id']


class PostSerializer(serializers.ModelSerializer):
    # Serializes a post in the way the API specifies.
    comments = serializers.SerializerMethodField('paginated_comment')
    author = AuthorSerializer()

    class Meta:
        model = Post
        fields = ['title', 'source', 'origin', 'description', 'contentType',
                  'content',  'author', 'categories', 'comments']

    # From: https://stackoverflow.com/a/49677960
    def paginated_comment(self, obj):
        page_size = self.context['request'].query_params.get(
            'size') or 50  # Default page size is 50
        paginator = Paginator(obj.comment_set.all(), page_size)
        page = self.context['request'].query_params.get(
            'page') or 1  # This should be 0, we will see though

        comments_in_page = paginator.page(page)
        serializer = CommentSerializer(comments_in_page, many=True)

        return serializer.data
