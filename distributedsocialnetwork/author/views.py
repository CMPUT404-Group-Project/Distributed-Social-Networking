from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.urls import reverse_lazy

from .forms import AuthorCreationForm, AuthorChangeForm, AuthorAuthenticationForm
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
            author = authenticate(displayName=displayName, password=raw_password, email=email, first_name=first_name, last_name=last_name, github=github)
            # login(request, author) # Cannot log in since is_active is default to false, admin has to accept before they can login
            return redirect(reverse_lazy('home'))
        else:
            context['form'] = form

    else:
        form = AuthorCreationForm()
        context['form'] = form

    return render(request, 'register.html', context)

def changeAuthorView(request):
    if not request.user.is_authenticated:
        return redirect(reverse_lazy('login'))
    
    context = {}

    if request.POST:
        form = AuthorChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(reverse_lazy('home'))
    else:
        form = AuthorChangeForm(
            initial = {
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "github": request.user.github,
            }
        )

    context['updateForm'] = form
    return render(request, 'update.html', context)

def loginView(request):
    context = {}

    user = request.user
    if user.is_authenticated:
        return redirect(reverse_lazy('home'))

    if request.POST:
        form = AuthorAuthenticationForm(request.POST)
        if form.is_valid():
            displayName = request.POST['displayName']
            password = request.POST['password']
            user = authenticate(displayName=displayName, password=password)

            if user:
                login(request, user)
                return redirect(reverse_lazy('home'))
    else:
        form = AuthorAuthenticationForm()

    context['loginForm'] = form
    return render(request, 'login.html', context)

def logoutView(request):
    logout(request)
    return redirect(reverse_lazy('home'))