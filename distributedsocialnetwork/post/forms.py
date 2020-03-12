from django.forms import ModelForm
from .models import Post


class PostCreationForm(ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'description', 'contentType',
                  'content', 'categories', 'visibility', 'visibleTo')

class PostCommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('commentContent')
