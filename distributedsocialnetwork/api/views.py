from django.shortcuts import render
from rest_framework.mixins import(
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.pagination import PageNumberPagination
from post.models import Post, Comment
from post.serializers import PostSerializer, CommentSerializer
from collections import OrderedDict
# Create your views here.


class PostPageNumberPagination(PageNumberPagination):
    # Custom PageNumberPagination for posts
    # page_size = 1
    page_size_query_param = 'size'

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'size': self.page_size,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'posts': data

        })


class PostViewSet(GenericViewSet, ListModelMixin):
    serializer_class = PostSerializer
    pagination_class = PostPageNumberPagination
    queryset = Post.objects.filter(visibility="PUBLIC")
