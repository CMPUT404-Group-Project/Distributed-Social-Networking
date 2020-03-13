from django.forms import ModelForm
from django import forms
from .models import Post, Comment
from author.models import Author


class PostCreationForm(ModelForm):
    # visibleTo is a comma-separated list of author ids -- we render this as a ModelMultipleChoiceField and then
    # modify it to fit our model
    visibleTo = forms.ModelMultipleChoiceField(queryset=Author.objects.all())

    class Meta:
        model = Post
        fields = ('title', 'description', 'contentType',
                  'content', 'categories', 'visibility', 'visibleTo')

    def __init__(self, *args, **kwargs):
        super(PostCreationForm, self).__init__(*args, **kwargs)
        self.fields['visibleTo'].label = "Who Can See This Post (Private posts only, hold Shift/Ctrl to select more)"
        self.fields["contentType"].label = "Content Type"
        self.fields["categories"].label = "Categories (comma-separated)"
        self.fields["categories"].required = False
        self.fields["visibleTo"].required = False

    def clean_visibleTo(self):
        # We convert the selected authors into their ids and concatenate them into a commaseparated string
        if self.cleaned_data.get("visibility") != "PRIVATE":
            return ""
        author_list = list(self.cleaned_data.get('visibleTo'))
        charfield_string = ""
        for author in author_list:
            charfield_string += str(author.id) + ','
        charfield_string = charfield_string[:-1]
        return charfield_string


class PostCommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('comment', 'contentType')
