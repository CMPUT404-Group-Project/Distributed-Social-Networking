from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from post.models import Post
from post.serializers import PostSerializer
# Create your views here.


class PublicPostView(generics.ListCreateAPIView):
    # Requesting /posts. GET returns the list of publicly accessible posts, POST/PUT (should) insert them
    serializer_class = PostSerializer
    model = Post
    queryset = model.objects.filter(visibility="PUBLIC")


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    # Detailed view of a Post. /posts/<id>. GET returns the Post, POST/PUT (should) insert them
    serializer_class = PostSerializer
    model = Post
    queryset = model.objects.all()
