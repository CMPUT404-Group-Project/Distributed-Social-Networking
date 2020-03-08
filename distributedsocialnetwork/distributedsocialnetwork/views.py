from django.shortcuts import render


def index(request):
    context = {}

    # authors = Author.objects.all()
    # context['authors'] = authors

    return render(request, 'index.html', context)
