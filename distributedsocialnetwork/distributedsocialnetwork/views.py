from django.shortcuts import render
from author.models import Author
from post.models import Post


def index(request):
    context = {}

    authors = Author.objects.all()
    context['authors'] = authors
    posts = Post.objects.all()
    context['posts'] = posts

    return render(request, 'index.html', context)
