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
        following = Follower.objects.filter(
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
        if len(Friend.objects.filter(current=author)) == 0:
            # No friends :(
            return []
        friend_object = Friend.objects.get(current=author)
        return list(friend_object.other.all())

    def add_friend(self, current_author, other_author):
        # We delete all notions of following in the Connection db and replace with new ones where they are friends
        Follower.objects.filter(models.Q(current=current_author, other=other_author) |
                                models.Q(current=other_author, other=current_author)).delete()
        friend_object = Friend.objects.get_or_create(current=current_author)[0]
        friend_object.other.add(other_author)
        friend_object.save()
        # We also have to save a friend object for the other friend
        other_friend_object = Friend.objects.get_or_create(
            current=other_author)[0]
        other_friend_object.other.add(current_author)
        other_friend_object.save()

    def remove_friend(self, current_author, other_author):
        # We remove them as a friend. They remain in the database as a follower.
        if len(Friend.objects.filter(current=current_author)) != 0:
            friend_object = Friend.objects.get(current=current_author)
            friend_object.other.remove(other_author)
            # We also have to remove the current author from the other friend object
            if len(Friend.objects.filter(current=other_author)) != 0:
                other_friend_object = Friend.objects.get(current=other_author)
                other_friend_object.other.remove(current_author)
        # We also create a new Follower instance, since that friend is technically still following us
        Follower.objects.create(current=other_author, other=current_author)

    def are_friends(self, current_author, other_author):
        # Check to see if they are friends
        if len(Friend.objects.filter(current=current_author)) < 1:
            return False
        friend_object = Friend.objects.get(current=current_author)
        return (other_author in friend_object.other.all())

    def get_foaf(self, author):
        # Return a list of all people considered who can see a FOAF post of an author
        # I interpret this as to allowing friends AND friends of friends to see your post
        friends = Friend.objects.get_friends(author)
        foaf_set = set(friends)
        for friend in friends:
            friends_of_friends = set(Friend.objects.get_friends(friend))
            foaf_set = foaf_set | friends_of_friends
        return list(foaf_set)


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
        Author, on_delete=models.CASCADE, related_name="current_author")
    other = models.ManyToManyField(Author)
    objects = FriendManager()
