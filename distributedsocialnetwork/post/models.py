import uuid
import datetime
from django.db import models
from author.models import Author

# Create your models here.


class Post(models.Model):
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    source = models.URLField(max_length=100)
    origin = models.URLField(max_length=100)
    description = models.CharField(max_length=120)
    contentType = models.CharField(
        max_length=20, choices=CONTENT_TYPE_CHOICES, default='text/plain')
    content = models.TextField()
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    categories = models.CharField(max_length=200, blank=True)
    published = models.DateTimeField()
    visibility = models.CharField(
        max_length=10, choices=VISIBILITY_CHOICES, default="PUBLIC")
    visibleTo = models.CharField(max_length=200, blank=True)
    unlisted = models.BooleanField(default=False)

    class Meta:
        # This orders posts by the time they were published, in descending order
        ordering = ['-published']

    def __str__(self):
        return self.title

    def create(self, args, **kwargs):
        # This is to ensure that we can insert our own timestamps into the published field
        if published == None:
            published = datetime.datetime.now()
        super(Post, self).save(args, **kwargs)


class Comment(models.Model):
    generatedUUID = uuid.uuid4().hex
    CONTENT_TYPE_CHOICES = [
        ('text/markdown', 'text/markdown'),
        ('text/plain', 'text/plain'),
        ('application/base64', 'application/base64'),
        ('image/png;base64', 'image/png;base64'),
        ('image/jpeg;base64', 'image/jpeg;base64'),
    ]
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    comment = models.TextField()
    published = models.DateTimeField()
    contentType = models.CharField(
        max_length=20, choices=CONTENT_TYPE_CHOICES, default='text/plain')
    post_id = models.ForeignKey(
        Post, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    def __str__(self):
        return str(self.author) + str(self.published)

    def create(self, args, **kwargs):
        # This is to ensure that we can insert our own timestamps into the published field
        if published == None:
            published = datetime.datetime.now()
        super(Comment, self).save(args, **kwargs)
