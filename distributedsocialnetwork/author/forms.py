from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import Author


class AuthorCreationForm(UserCreationForm):
    displayName = forms.CharField(max_length=150, help_text="Required. Enter a display name.")
    email = forms.EmailField(max_length=255, help_text="Required. Enter a valid email address.")
    first_name = forms.CharField(max_length=30, help_text="Required. Enter your first name.")
    last_name = forms.CharField(max_length=150, help_text="Required. Enter your last name.")
    github = forms.CharField(max_length=255, help_text="Enter your GitHub profile url.")

    class Meta(UserCreationForm):
        model = Author
        fields = ('displayName',
                'email',
                'first_name',
                'last_name',
                'github',
                'password1',
                'password2'
                )


class AuthorChangeForm(UserChangeForm):

    class Meta:
        model = Author
        fields = ('github',
                'is_active',
                'is_staff',
                )