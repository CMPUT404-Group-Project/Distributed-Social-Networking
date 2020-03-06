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
    author = serializers.SlugRelatedField(
        queryset=Author.objects.all(), slug_field='id')

    class Meta:
        model = Comment
        fields = ['author', 'comment', 'contentType',
                  'post_id', 'published', 'id']

    # # For representing authors properly
    # # Thanks to Sardorbek Imomaliev: https://stackoverflow.com/a/50257132
    def to_representation(self, instance):
        self.fields['author'] = AuthorSerializer(read_only=True)
        return super(CommentSerializer, self).to_representation(instance)

    def create(self, validated_data):
        return Comment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.author = validated_data.get('author', instance.author)
        instance.comment = validated_data.get('comment', instance.comment)
        instance.contentType = validated_data.get(
            'contentType', instance.contentType)
        instance.post_id = validated_data.get("post_id", instance.post_id)
        instance.save()
        return instance

    # Validation of a comment
    # POSTed in this form:
    # {
    #     "query": "addComment",
    #     "post":"http://whereitcamefrom.com/posts/zzzzz",
    #     "comment":{
    #         "author":{
    #             # ID of the Author
    #                 "id":"http://127.0.0.1:5454/author/1d698d25ff008f7538453c120f581471",
    #                 "host":"http://127.0.0.1:5454/",
    #                 "displayName":"Greg Johnson",
    #                 # url to the authors information
    #                 "url":"http://127.0.0.1:5454/author/1d698d25ff008f7538453c120f581471",
    #                 # HATEOS url for Github API
    #                 "github": "http://github.com/gjohnson"
    #         },
    #         "comment":"Sick Olde English",
    #         "contentType":"text/markdown",
    #         # ISO 8601 TIMESTAMP
    #         "published":"2015-03-09T13:07:04+00:00",
    #         # ID of the Comment (UUID)
    #         "id":"de305d54-75b4-431b-adb2-eb6b9e546013"
    #     }
    # }
    def validate_author(self, value):
        # Author
        # We mainly care about whether the author exists
        print("HEHEHEAHSEKAJSDLKJASDLKJNASASDJASJDASLKDJALSKDJALSKDJALSKDJALSKDJ")
        return value


class PostSerializer(serializers.ModelSerializer):
    # Serializes a post in the way the API specifies.
    # author = AuthorSerializer()
    author = serializers.SlugRelatedField(
        queryset=Author.objects.all(), slug_field='id')

    class Meta:
        model = Post
        fields = ['title', 'source', 'origin', 'description', 'contentType',
                  'content',  'author', 'categories', 'published',
                  'visibility', 'id', 'visibleTo']

    # For representing authors properly
    # Thanks to Sardorbek Imomaliev: https://stackoverflow.com/a/50257132

    def to_representation(self, instance):
        self.fields['author'] = AuthorSerializer(read_only=True)
        return super(PostSerializer, self).to_representation(instance)

    def create(self, validated_data):
        return Post.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.source = validated_data.get('source', instance.source)
        instance.origin = validated_data.get('origin', instance.origin)
        instance.description = validated_data.get(
            'description', instance.description)
        instance.contentType = validated_data.get(
            'contentType', instance.contentType)
        instance.content = validated_data.get('content', instance.content)
        instance.author = validated_data.get('author', instance.author)
        instance.visibility = validated_data.get(
            'visibility', instance.visibility)
        instance.save()
        return instance
