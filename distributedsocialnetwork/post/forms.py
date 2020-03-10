from django.forms import ModelForm
from .models import Post


class PostCreationForm(ModelForm):
    # title = forms.CharField(
    #     max_length=100, help_text="Enter a captivating title.")
    # description = forms.CharField(
    #     max_length=120, help_text="Required. Enter a valid email address.")
    # cententType = forms.CharField(
    #     max_length=20, choices=Post.CONTENT_TYPE_CHOICES, default='text/plain')
    # content = forms.Textarea()
    # catagories = forms.CharField(
    #     max_length=200, help_text="status,family,bitcoin,examples,etc", required=False)

    class Meta:
        model = Post
        fields = ('title', 'description', 'contentType',
                  'content', 'categories', 'visibility', 'visibleTo')
