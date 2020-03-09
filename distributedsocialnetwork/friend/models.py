from django.db import models
from author.models import Author


# Create your models here.

# Based off of the second method described by Brian Caffey here: https://briancaffey.github.io/2017/07/19/different-ways-to-build-friend-models-in-django.html

class FollowerManager(models.Manager):
    # For friends/follower management

    def get_followers(self, author):
        # Return the authors following you
        followers = Follower.objects.fitler(
            other=author)
        authors = []
        for connection in followers:
            authors.append(connection.current)
        return authors

    def get_following(self, author):
        # Return the authors you are following
        following = Connection.objects.filter(
            current=author)
        authors = []
        for connection in following:
            authors.append(connection.other)
        return authors

    def add_follower(self, current_author, other_author):
        # Add a new follower (unrequited friend requests)
        Follower.objects.create(
            current=other_author, other=current_author)

    def add_following(self, current_author, other_author):
        # Add a new author to follow (friend request sent)
        Follower.objects.create(
            current=current_author, other=other_author)

    def is_following(self, current_author, other_author):
        # Returns bool for if current author is following the other author
        return len(Follower.objects.filter(current=current_author, other=other_author)) == 1

    def is_followed(self, current_author, other_author):
        # Returns bool for iff current author is being followed by the other author
        return len(Follower.objects.filter(current=other_author, other=current_author)) == 1


class FriendManager(models.Manager):

    def get_friends(self, author):
        # Return your friends
        friends = Friend.objects.filter(
            models.Q(current=author) |
            models.Q(other=author))
        authors = []
        for connection in friends:
            authors.append(connection.other)
        return authors

    def add_friend(self, current_author, other_author):
        # We delete all notions of following in the Connection db and replace with new ones where they are friends
        Follower.objects.filter(models.Q(current=current_author, other=other_author) |
                                models.Q(current=other_author, other=current_author)).delete()
        Friend.objects.create(
            current=current_author, other=other_author)

    def remove_friend(self, current_author, other_author):
        # We remove them as a friend. They remain in the database as a follower.
        Friend.objects.filter(models.Q(current=current_author, other=other_author) |
                              models.Q(current=other_author, other=current_author)).delete()
        Follower.objects.create(
            current=other_author, other=current_author)

    def are_friends(self, current_author, other_author):
        # Check to see if they are friends
        return len(Friend.objects.filter(current=current_author, other=other_author)) == 1


class Follower(models.Model):

    # We are storing follows (unrequited friend requests) in here
    # Author A follows author B --> Author A can see all of Author B's public posts in their stream
    # Current follows other!
    current = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name="current_author_follower")
    other = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name="other_author_follower")
    objects = FollowerManager()


class Friend(models.Model):
    # We are storing friends in here
    # Current is friends with other!
    current = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name="current_author_friend")
    other = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name="other_author_friend")
    objects = FriendManager()
