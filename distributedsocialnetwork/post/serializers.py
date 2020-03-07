# Serializers for Posts and Comments
import datetime
from rest_framework import serializers, fields
from .models import Post, Comment
from author.models import Author
from author.serializers import AuthorSerializer


class CommentSerializer(serializers.ModelSerializer):
    # Serializes a comment in the way the API specifies.
    author = serializers.SlugRelatedField(
        queryset=Author.objects.all(), slug_field='id')
    # Allows us to overwrite the autogenerated UUID, for POST
    id = serializers.UUIDField()
    published = fields.DateTimeField()

    class Meta:
        model = Comment
        fields = ['author', 'comment', 'contentType',
                  'post_id', 'published', 'id']

    # # For representing authors properly
    # # Thanks to Sardorbek Imomaliev: https://stackoverflow.com/a/50257132
    def to_representation(self, instance):
        self.fields['author'] = AuthorSerializer(read_only=True)
        return super(CommentSerializer, self).to_representation(instance)

    def validate(self, data):
        # We will perform a few checks, and then call the super to do the rest
        # Is the Post ID correct?
        post_id = self.context["pk"]
        if post_id != data["post_id"].id:
            raise serializers.ValidationError(
                "You cannot post a comment to a different post. ID given was " + str(data["post_id"].id) + ' and URI was for '+str(post_pk))
        return super(CommentSerializer, self).validate(data)


class PostSerializer(serializers.ModelSerializer):
    # Serializes a post in the way the API specifies.
    author = serializers.SlugRelatedField(
        queryset=Author.objects.all(), slug_field='id')
    id = serializers.UUIDField()
    published = fields.DateTimeField()

    class Meta:
        model = Post
        fields = ['title', 'source', 'origin', 'description', 'contentType',
                  'content',  'author', 'categories', 'published',
                  'visibility', 'id', 'visibleTo', 'unlisted']

    # For representing authors properly
    # Thanks to Sardorbek Imomaliev: https://stackoverflow.com/a/50257132
    def to_representation(self, instance):
        self.fields['author'] = AuthorSerializer(read_only=True)
        return super(PostSerializer, self).to_representation(instance)
