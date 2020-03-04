from django.db import models
from author.models import Author
import uuid
# Create your models here.


class Post(models.Model):
    generatedUUID = uuid.uuid4().hex

    CONTENT_TYPE_CHOICES = [
        ('text/markdown', 'text/markdown'),
        ('text/plain', 'text/plain'),
        ('application/base64', 'application/base64'),
        ('image/png;base64', 'image/png;base64'),
        ('image/jpeg;base64', 'image/jpeg;base64'),
    ]
    VISIBILITY_CHOICES = [
        ("PUBLIC", "Public"),
        ("FOAF", "Friends of Friends"),
        ("FRIENDS", "Friends Only"),
        ("PRIVATE", "Private"),
        ("SERVERONLY", "Server Only"),
    ]

    title = models.CharField(max_length=100)
    source = models.URLField(max_length=100)
    origin = models.URLField(max_length=100)
    description = models.CharField(max_length=120)
    contentType = models.CharField(
        max_length=20, choices=CONTENT_TYPE_CHOICES, default='text/plain')
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    categories = models.CharField(max_length=200)

    # TODO: once we have a comments model we can add this in
    # comments = models.ForeignKey(Comment, on_delete=models.CASCADE)
    # count ==> the total number of comments
    # next ==> the next page of comments to load
    size = models.IntegerField(default=50)  # The number of comments per page
    published = models.DateTimeField(auto_now=True)
    id = models.CharField(max_length=32, default=generatedUUID,
                          editable=False, unique=True, primary_key=True)
    visibility = models.CharField(
        max_length=10, choices=VISIBILITY_CHOICES, default="PUBLIC")
    visibleTo = models.CharField(max_length=200, blank=True)
    unlisted = models.BooleanField(default=False)

    class Meta:
        # This orders posts by the time they were published, in descending order
        ordering = ['-published']

    def __str__(self):
        return self.title
