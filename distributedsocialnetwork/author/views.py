from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout

from .forms import AuthorCreationForm, AuthorChangeForm
from .models import Author


def index(request):
    context = {}

    authors = Author.objects.all()
    context['authors'] = authors

    return render(request, 'index.html', context)


def createAuthorView(request):
    context = {}

    if request.POST:
        form = AuthorCreationForm(request.POST)
        if form.is_valid():
            form.save()
            displayName = form.cleaned_data.get('displayName')
            email = form.cleaned_data.get('email')
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            github = form.cleaned_data.get('github')
            raw_password = form.cleaned_data.get('password1')
            author = authenticate(displayName, password=raw_password)
            login(request, author)
            return redirect('home')
        else:
            context['form'] = form
    else:
        form = AuthorCreationForm()
        context['form'] = form

    return render(request, 'register.html', context)

def logoutView(request):
    logout(request)
    return redirect('home')