from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import authenticate
from django import forms
from .models import Author


class AuthorCreationForm(UserCreationForm):
    displayName = forms.CharField(
        max_length=150, help_text="Required. Enter a display name.")
    email = forms.EmailField(
        max_length=255, help_text="Required. Enter a valid email address.")
    first_name = forms.CharField(
        max_length=30, help_text="Required. Enter your first name.")
    last_name = forms.CharField(
        max_length=150, help_text="Required. Enter your last name.")
    github = forms.CharField(
        max_length=255, help_text="Enter your GitHub profile url.", required=False)

    class Meta(UserCreationForm):
        model = Author
        fields = ('displayName', 'email', 'first_name',
                  'last_name', 'github', 'password1', 'password2')


class AuthorChangeForm(UserChangeForm):
    first_name = forms.CharField(
        max_length=30, help_text="Required. Enter your first name.")
    last_name = forms.CharField(
        max_length=150, help_text="Required. Enter your last name.")
    github = forms.CharField(
        max_length=255, help_text="Enter your GitHub profile url.", required=False)
    password = None

    class Meta(UserChangeForm):
        model = Author
        fields = ('first_name', 'last_name', 'github')


class AuthorAuthenticationForm(forms.ModelForm):
    displayName = forms.CharField(
        max_length=150, help_text="Required. Enter a display name.")
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    class Meta:
        model = Author
        fields = ('displayName', 'password')

    def clean(self):
        if self.is_valid():
            displayName = self.cleaned_data['displayName']
            password = self.cleaned_data['password']

            if not authenticate(displayName=displayName, password=password):
                raise forms.ValidationError("Invalid login.")
