from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import authenticate
from django import forms
from .models import Author


class AuthorCreationForm(UserCreationForm):
    displayName = forms.CharField(
        max_length=150, help_text="Required. Enter a display name.")
    email = forms.EmailField(
        max_length=255, help_text="Enter a valid email address.", required=False)
    first_name = forms.CharField(
        max_length=30, help_text="Enter your first name.", required=False)
    last_name = forms.CharField(
        max_length=150, help_text="Enter your last name.", required=False)
    github = forms.URLField(
        max_length=255, help_text="Enter your GitHub profile url (e.g., http://github.com/username).", required=False)

    class Meta(UserCreationForm):
        model = Author
        fields = ('displayName', 'email', 'first_name',
                  'last_name', 'github', 'password1', 'password2')


class AuthorChangeForm(UserChangeForm):
    first_name = forms.CharField(
        max_length=30, help_text="Enter your first name.", required=False)
    last_name = forms.CharField(
        max_length=150, help_text="Enter your last name.", required=False)
    github = forms.URLField(
        max_length=255, help_text="Enter your GitHub profile url (e.g., http://github.com/username).", required=False)
    bio = forms.CharField(
        max_length=160, help_text="Enter a short bio.", required=False)
    password = None

    class Meta(UserChangeForm):
        model = Author
        fields = ('first_name', 'last_name', 'github', 'bio')


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
            user = authenticate(displayName=displayName, password=password)
            if user is not None:
                if not user.is_active:
                    raise forms.ValidationError(
                        "Your account has not been activated please contact an admin.")
            else:
                raise forms.ValidationError(
                    "Username or password is incorrect.")
