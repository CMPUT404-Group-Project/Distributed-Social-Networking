from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.urls import reverse_lazy
from .forms import PostCreationForm
# Create your views here.


def create(request):
    context = {}

    user = request.user
    if user.is_authenticated:
        return redirect(reverse_lazy('home'))

    if request.POST:
        form = PostCreationForm(request.POST)
        if form.is_valid():
            display_name = request.POST['displayName']
            password = request.POST['password']
            user = authenticate(displayName=display_name, password=password)

            if user:
                login(request, user)
                return redirect(reverse_lazy('home'))
    else:
        form = PostCreationForm()

    context['postCreationForm'] = form
    return render(request, 'create.html', context)
