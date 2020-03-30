import uuid
import datetime
import pytz
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from author.models import Author
from post.models import Post, Comment
from friend.models import Friend, Follower
from node.models import Node
from django.conf import settings
import urllib

# Create your tests here.


class VisiblePosts(APITestCase):
    def setUp(self):

        self.testUserId = 'http://testserver.com/author/' + \
            str(uuid.uuid4().hex)
        self.testAuthor = Author.objects.create(id=self.testUserId, host="http://google.com", url="http://url.com",
                                                displayName="Testmaster", github="http://github.com/what")
        # Post 1
        self.post_id1 = uuid.uuid4().hex
        self.title1 = "Test1"
        self.source1 = settings.FORMATTED_HOST_NAME
        self.origin1 = settings.FORMATTED_HOST_NAME
        self.description1 = 'Description1'
        self.contentType1 = "text/plain"
        self.content1 = "Content of the first test case post"
        self.author1 = self.testAuthor
        self.categories1 = "first,second"
        self.published1 = datetime.datetime(
            2019, 1, 1, 1, 1, 1, tzinfo=pytz.UTC)
        self.visibility1 = "PUBLIC"
        self.visibleTo1 = ""
        self.unlisted1 = False
        Post.objects.create(id=self.post_id1, title=self.title1,
                            source=self.source1, origin=self.origin1,
                            description=self.description1, contentType=self.contentType1,
                            content=self.content1, author=self.author1, categories=self.categories1,
                            published=self.published1, visibility=self.visibility1, unlisted=self.unlisted1)

        # Post 2
        self.post_id2 = uuid.uuid4().hex
        self.title2 = "Test2"
        self.source2 = settings.FORMATTED_HOST_NAME
        self.origin2 = settings.FORMATTED_HOST_NAME
        self.description2 = 'Description2'
        self.contentType2 = "text/plain"
        self.content2 = "Content of the first test case post"
        self.author2 = self.testAuthor
        self.categories2 = "first"
        self.published2 = datetime.datetime(
            2020, 1, 1, 1, 1, 1, tzinfo=pytz.UTC)
        self.visibility2 = "PUBLIC"
        self.visibleTo2 = ""
        self.unlisted2 = False
        Post.objects.create(id=self.post_id2, title=self.title2,
                            source=self.source2, origin=self.origin2,
                            description=self.description2, contentType=self.contentType2,
                            content=self.content2, author=self.author2, categories=self.categories2,
                            published=self.published2, visibility=self.visibility2, unlisted=self.unlisted2)

        # Post 3 -- Private, so it shouldn't show
        self.post_id3 = uuid.uuid4().hex
        self.title3 = "Test3"
        self.source3 = settings.FORMATTED_HOST_NAME
        self.origin3 = settings.FORMATTED_HOST_NAME
        self.description3 = 'Description3'
        self.contentType3 = "text/plain"
        self.content3 = "Content of the first test case post"
        self.author3 = self.testAuthor
        self.categories3 = ""
        self.published3 = timezone.now()
        self.visibility3 = "PRIVATE"
        self.visibleTo3 = "jake,thatotherguy"
        self.unlisted3 = False
        Post.objects.create(id=self.post_id3, title=self.title3,
                            source=self.source3, origin=self.origin3,
                            description=self.description3, contentType=self.contentType3,
                            content=self.content3, author=self.author3, categories=self.categories3,
                            published=self.published3, visibility=self.visibility3, unlisted=self.unlisted3)

    def test_get_list(self):
        url = reverse('public-posts')
        response = self.client.get(url, format='json')
        # Test for response properly spent
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that all public posts have been retrieved
        self.assertEqual(len(response.data["posts"]), len(
            Post.objects.filter(visibility='PUBLIC')))
        # Test that the most recent public post is the top result in the posts list
        self.assertEqual(response.data["posts"][0]["title"], "Test2")
        # Test that the categories appear as a list of two elements
        self.assertEqual(response.data["posts"][1]["categories"][1], "second")
        # Test that there is an empty array of comments
        self.assertEqual(len(response.data["posts"][0]["comments"]), 0)
        # Test that there is a list of comments
        self.assertEqual(response.data["posts"][0]["next"],
                         'http://testserver' + url + '/' + response.data["posts"][0]["id"] + '/comments')
        # Test that each element of a given post is the same as what we inserted
        self.assertEqual(
            uuid.UUID(response.data["posts"][0]["id"]), uuid.UUID(self.post_id2))
        self.assertEqual(response.data["posts"][0]["title"], self.title2)
        self.assertEqual(response.data["posts"][0]["source"], self.source2)
        self.assertEqual(response.data["posts"][0]["origin"], self.origin2)
        self.assertEqual(response.data["posts"]
                         [0]["description"], self.description2)
        self.assertEqual(response.data["posts"]
                         [0]["contentType"], self.contentType2)
        self.assertEqual(response.data["posts"][0]["content"], self.content2)
        self.assertEqual(response.data["posts"]
                         [0]["categories"], self.categories2.split(','))
        self.assertEqual(response.data["posts"]
                         [0]["published"], self.published2.strftime('%Y-%m-%dT%H:%M:%S%z'))
        self.assertEqual(response.data["posts"]
                         [0]["visibility"], self.visibility2)
        self.assertEqual(len(response.data["posts"]
                             [0]["visibleTo"]), 0)
        self.assertEqual(response.data["posts"][0]["unlisted"], self.unlisted2)

    def test_get_list_pagination(self):
        url = reverse('public-posts') + '?size=1'
        response = self.client.get(url, format='json')

        # Test for response properly sent
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that we have retrieved one post
        self.assertEqual(len(response.data["posts"]), 1)
        # Test that we have a link to the next page, but not one to the previous page
        self.assertTrue("&page=1" in response.data["next"])
        self.assertFalse("previous" in response.data.keys())

        # Get the next page, then test for the opposite
        url = reverse('public-posts') + '?size=1&page=1'
        response = self.client.get(url, format='json')
        # Test for response properly sent
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that we have retrieved one post
        self.assertEqual(len(response.data["posts"]), 1)
        # Test that we have a link to the next page, but not one to the previous page
        self.assertTrue("&page=0" in response.data["previous"])
        self.assertFalse("next" in response.data.keys())


class PostDetailView(APITestCase):
    def setUp(self):
        self.testUserId = settings.FORMATTED_HOST_NAME + \
            str(uuid.uuid4().hex)
        self.foreignAuthorId = 'http://foreignsite.com/author/' + \
            str(uuid.uuid4().hex)
        self.testAuthor = Author.objects.create(id=self.testUserId, host=settings.FORMATTED_HOST_NAME, url=settings.FORMATTED_HOST_NAME,
                                                displayName="Testmaster", github="http://github.com/what")
        # We also want an author from another server, and a node with which to authenticate
        self.foreignAuthor = Author.objects.create(
            id=self.foreignAuthorId, host="http://foreignsite.com", url="http://foreignsite.com", displayName="ForeignAuthor", github="", email="wahtever@email.com")
        self.node = Node.objects.create(hostname="http://foreignsite.com",
                                        api_url="http://foreignsite.com", server_username="node", server_password="node")
        self.node_author = Author.objects.get(displayName="node")
        # Post 1
        self.post_id1_string = 'de305d54-75b4-431b-adb2-eb6b9e546013'
        self.post_id1 = uuid.UUID('de305d54-75b4-431b-adb2-eb6b9e546013')
        self.title1 = "Test1"
        self.source1 = settings.FORMATTED_HOST_NAME
        self.origin1 = settings.FORMATTED_HOST_NAME
        self.description1 = 'Description1'
        self.contentType1 = "text/plain"
        self.content1 = "Content of the first test case post"
        self.author1 = self.testAuthor
        self.categories1 = "first,second"
        self.published1 = datetime.datetime(
            2019, 1, 1, 1, 1, 1, tzinfo=pytz.UTC)
        self.visibility1 = "PUBLIC"
        self.visibleTo1 = ""
        self.unlisted1 = False
        Post.objects.create(id=self.post_id1, title=self.title1,
                            source=self.source1, origin=self.origin1,
                            description=self.description1, contentType=self.contentType1,
                            content=self.content1, author=self.author1, categories=self.categories1,
                            published=self.published1, visibility=self.visibility1, unlisted=self.unlisted1)
        # Post 2
        # This one is a private post, which the foreign user can see.
        self.post2 = Post.objects.create(id=uuid.UUID("73cc3f3c-0654-493f-a529-72413297ba55"), title="Test2",
                                         source=settings.FORMATTED_HOST_NAME, description="Description2", contentType="text/plain", content="Test content",
                                         author=self.author1, categories="",
                                         published=datetime.datetime(2019, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PRIVATE", visibleTo=self.foreignAuthorId, unlisted=False)
        # POST data, this is a valid post
        self.post_data = {
            "query": "addPost",
            "post": {
                "author": {
                    "id": str(self.testUserId),
                    "host": self.testAuthor.host,
                    "displayName": self.testAuthor.displayName,
                    "url": self.testAuthor.url,
                    "github": self.testAuthor.github
                },
                "title": "This one was made via a post!",
                "source": "http://google.com/fakeurl",
                "origin": "http://google.com/origin-of-post",
                "description": "This post is about cheese",
                "contentType": "text/plain",
                "content": "Wow what an amazing and insightful post this is",
                "categories": ["first", "second"],
                "published": "2015-03-09T13:07:04+00:00",
                "visibility": "PUBLIC",
                "visibleTo": "",
                "unlisted": False

            }
        }

    def test_get(self):
        url = '/api/posts/' + self.post_id1_string
        response = self.client.get(url, format='json')
        # Test for response properly spent
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that each element of a given post is the same as what we inserted
        self.assertEqual(
            uuid.UUID(response.data["posts"][0]["id"]), uuid.UUID(self.post_id1_string))
        self.assertEqual(response.data["posts"][0]["title"], self.title1)
        self.assertEqual(response.data["posts"][0]["source"], self.source1)
        self.assertEqual(response.data["posts"][0]["origin"], self.origin1)
        self.assertEqual(response.data["posts"]
                         [0]["description"], self.description1)
        self.assertEqual(response.data["posts"]
                         [0]["contentType"], self.contentType1)
        self.assertEqual(response.data["posts"][0]["content"], self.content1)
        self.assertEqual(response.data["posts"]
                         [0]["categories"], self.categories1.split(','))
        self.assertEqual(response.data["posts"]
                         [0]["published"], self.published1.strftime('%Y-%m-%dT%H:%M:%S%z'))
        self.assertEqual(response.data["posts"]
                         [0]["visibility"], self.visibility1)
        self.assertEqual(len(response.data["posts"]
                             [0]["visibleTo"]), 0)
        self.assertEqual(response.data["posts"][0]["unlisted"], self.unlisted1)
        # Test that there is an empty array of comments
        self.assertEqual(len(response.data["posts"][0]["comments"]), 0)
        # Test that there is a list of comments
        self.assertEqual(response.data["posts"][0]["next"],
                         'http://testserver' + url + '/comments')

    def test_get_private(self):
        # We should not be able to get the post without authenticating
        url = '/api/posts/' + str(self.post2.id)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # We should be able to authenticate as a node and get the private post
        self.client.force_authenticate(user=self.node_author)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["posts"]), 1)
        # We should also be able to see the post when authenticated as a user
        self.client.force_authenticate(user=self.foreignAuthor)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["posts"]), 1)

    def test_post_to_existing_uri(self):
        # This should fail
        self.client.force_authenticate(user=self.testAuthor)
        url = '/api/posts/' + self.post_id1_string

        response = self.client.post(url, self.post_data, format='json')
        # Test to ensure that this post has not been inserted
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_to_new_uri(self):
        # This should succeed and return a 201 Created
        self.client.force_authenticate(user=self.testAuthor)
        new_post_id = self.post_id1_string[:-1] + '4'
        url = '/api/posts/' + new_post_id
        response = self.client.post(url, self.post_data, format='json')
        # Test to ensure that this post has been inserted
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Test that this new post has entered the database
        self.assertEqual(Post.objects.filter(id=new_post_id).count(), 1)

    def test_post_invalid_format(self):
        self.client.force_authenticate(user=self.testAuthor)
        new_post_id = self.post_id1_string[:-1] + '5'
        invalid_post = {
            "query": "addPost",
            "post": {
                "author": {
                    "id": self.testUserId,
                    "host": self.testAuthor.host,
                    "displayName": self.testAuthor.displayName,
                    "url": self.testAuthor.url,
                    "github": self.testAuthor.github
                },
                "source": "http://google.com/fakeurl",
                "origin": "http://google.com/origin-of-post",
                "description": "This post is about cheese",
                "contentType": "text/plain",
                "content": "Wow what an amazing and insightful post this is",
                "categories": ["first", "second"],
                "published": "2015-03-09T13:07:04+00:00",
                "visibility": "PUBLIC",
                "visibleTo": "",
                "unlisted": False

            }
        }
        url = '/api/posts/' + new_post_id
        response = self.client.post(url, invalid_post, format='json')
        # We don't have a title set, so it should fail to create the post
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_unauthorized(self):
        # This should return 401 UNAUTHORIZED
        new_post_id = self.post_id1_string[:-1] + '5'
        url = '/api/posts/' + new_post_id
        response = self.client.post(url, self.post_data, format='json')
        # Test to ensure that this post has been inserted
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # Test that no new post was created
        self.assertEqual(Post.objects.filter(id=new_post_id).count(), 0)

    def test_put_valid_format(self):
        self.client.force_authenticate(user=self.testAuthor)
        post_data = {
            "query": "addPost",
            "post": {
                "author": {
                    "id": str(self.testUserId),
                    "host": self.testAuthor.host,
                    "displayName": self.testAuthor.displayName,
                    "url": self.testAuthor.url,
                    "github": self.testAuthor.github
                },
                "title": "This is the updated title!",
                "source": "http://google.com/fakeurl",
                "origin": "http://google.com/origin-of-post",
                "description": "This post is about cheese",
                "contentType": "text/markdown",
                "content": "Wow what an amazing and insightful post this is",
                "categories": ["first", "second"],
                "published": "2015-03-09T13:07:04+00:00",
                "visibility": "PUBLIC",
                "visibleTo": "",
                "unlisted": False

            }
        }
        url = '/api/posts/' + self.post_id1_string
        response = self.client.put(url, post_data, format='json')
        # Check that it responds with 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that it actually updated
        post = Post.objects.filter(id=self.post_id1)[0]
        self.assertEqual(post.title, "This is the updated title!")

    def test_put_invalid_format(self):
        self.client.force_authenticate(user=self.testAuthor)
        post_data = {
            "query": "addPost",
            "post": {
                "author": {
                    "id": str(self.testUserId),
                    "host": self.testAuthor.host,
                    "displayName": self.testAuthor.displayName,
                    "url": self.testAuthor.url,
                    "github": self.testAuthor.github
                },
                "source": "http://google.com/fakeurl",
                "origin": "http://google.com/origin-of-post",
                "description": "This post is about cheese",
                "contentType": "text/markdown",
                "content": "Wow what an amazing and insightful post this is",
                "categories": ["first", "second"],
                "published": timezone.now(),
                "visibility": "PUBLIC",
                "visibleTo": "",
                "unlisted": False

            }
        }
        url = '/api/posts/' + self.post_id1_string
        response = self.client.put(url, post_data, format='json')
        # We don't have a title set, so it should fail to create the post
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Let's ensure it didn't update the post
        post = Post.objects.filter(id=self.post_id1)[0]
        self.assertNotEqual(post.title, "This is the updated title!")

    def test_put_unauthorized(self):
        # This should fail and return a 401 UNAUTHORIZED
        post_data = {
            "query": "addPost",
            "post": {
                "author": {
                    "id": str(self.testUserId),
                    "host": self.testAuthor.host,
                    "displayName": self.testAuthor.displayName,
                    "url": self.testAuthor.url,
                    "github": self.testAuthor.github
                },
                "title": "This is the updated title!",
                "source": "http://google.com/fakeurl",
                "origin": "http://google.com/origin-of-post",
                "description": "This post is about cheese",
                "contentType": "text/markdown",
                "content": "Wow what an amazing and insightful post this is",
                "categories": ["first", "second"],
                "published": "2015-03-09T13:07:04+00:00",
                "visibility": "PUBLIC",
                "visibleTo": "",
                "unlisted": False

            }
        }
        url = '/api/posts/' + self.post_id1_string
        response = self.client.put(url, post_data, format='json')
        # Should get a 401 UNAUTHORIZED
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # Let's ensure it didn't update the post
        post = Post.objects.filter(id=self.post_id1)[0]
        self.assertNotEqual(post.title, "This is the updated title!")

    def test_delete_post(self):
        # This should succeed and return a 200 OK
        # Authenticate as testAuthor
        self.client.force_authenticate(user=self.testAuthor)
        new_post_id = self.post_id1_string[:-1] + '6'
        url = '/api/posts/' + new_post_id
        self.client.post(url, self.post_data, format='json')
        # Test that this new post is in the database
        self.assertEqual(Post.objects.filter(id=new_post_id).count(), 1)
        response = self.client.delete(url, format='json')
        # Test to ensure that this post has been deleted
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that this new post is no longer in the database
        self.assertEqual(Post.objects.filter(id=new_post_id).count(), 0)

    def test_delete_post_unauthorized(self):
        # This should fail and return a 401 UNAUTHORIZED
        new_post_id = self.post_id1_string[:-1] + '7'
        url = '/api/posts/' + new_post_id
        # Login and create a new post
        self.client.force_authenticate(user=self.testAuthor)
        self.client.post(url, self.post_data, format='json')
        # Test that this new post is in the database
        self.assertEqual(Post.objects.filter(id=new_post_id).count(), 1)
        # Log out
        self.client.logout()
        response = self.client.delete(url, format='json')
        # Test to see if we get a 401 back.
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # Post should still exist:
        self.assertEqual(Post.objects.filter(id=new_post_id).count(), 1)

    def test_delete_post_invalid_uri(self):
        new_post_id = self.post_id1_string[:-1] + '8'
        url = '/api/posts/' + new_post_id
        response = self.client.delete(url, format='json')
        # This post doesn't exist, so we should get a 404 back
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Test that this post isn't in the database
        self.assertEqual(Post.objects.filter(id=new_post_id).count(), 0)


class CommentList(APITestCase):
    def setUp(self):
        self.testUserId = 'http://testserver.com/author/' + \
            str(uuid.uuid4().hex)
        self.testAuthor = Author.objects.create(id=self.testUserId, host="http://google.com", url="http://url.com",
                                                displayName="Testmaster", github="http://github.com/what")
        # Post
        self.post_id_string = "de305d54-75b4-431b-adb2-eb6b9e546012"
        self.post_id = uuid.UUID('de305d54-75b4-431b-adb2-eb6b9e546012')
        self.post_title = "Test1"
        self.post_source = 'http://testcase1.com'
        self.post_origin = 'http://testcase1.com/original'
        self.post_description = 'Description1'
        self.post_contentType = "text/plain"
        self.post_content = "Content of the first test case post"
        self.post_author = self.testAuthor
        self.post_categories = "first,second"
        self.post_published = datetime.datetime(
            2019, 1, 1, 1, 1, 1, tzinfo=pytz.UTC)
        self.post_visibility = "PUBLIC"
        self.post_visibleTo = ""
        self.post_unlisted = False
        self.post = Post.objects.create(id=self.post_id, title=self.post_title,
                                        source=self.post_source, origin=self.post_origin,
                                        description=self.post_description, contentType=self.post_contentType,
                                        content=self.post_content, author=self.post_author, categories=self.post_categories,
                                        published=self.post_published, visibility=self.post_visibility, unlisted=self.post_unlisted)

        # We create a couple of comments for out post
        self.comment1_id_string = "de305d54-75b4-431b-adb2-eb6b9e546011"
        self.comment1_id = uuid.UUID("de305d54-75b4-431b-adb2-eb6b9e546011")
        self.comment1_comment = "This is the first comment"
        self.comment1_published = datetime.datetime(
            2020, 1, 1, 1, 1, 1, tzinfo=pytz.UTC)
        self.comment1_contentType = "text/plain"
        self.comment1_post_id = self.post
        Comment.objects.create(id=self.comment1_id, comment=self.comment1_comment,
                               published=self.comment1_published, contentType=self.comment1_contentType, post_id=self.comment1_post_id, author=self.testAuthor)

        self.comment2_id_string = "de305d54-75b4-431b-adb2-eb6b9e546010"
        self.comment2_id = uuid.UUID("de305d54-75b4-431b-adb2-eb6b9e546010")
        self.comment2_comment = "This is the second comment"
        self.comment2_published = datetime.datetime(
            2019, 1, 1, 1, 1, 1, tzinfo=pytz.UTC)
        self.comment2_contentType = "text/plain"
        self.comment2_post_id = self.post
        Comment.objects.create(id=self.comment2_id, comment=self.comment2_comment,
                               published=self.comment2_published, contentType=self.comment2_contentType, post_id=self.comment2_post_id, author=self.testAuthor)

    def test_get_list(self):
        url = '/api/posts/de305d54-75b4-431b-adb2-eb6b9e546012/comments'
        response = self.client.get(url, format='json')
        # Test for response properly sent
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that all public posts have been retrieved
        self.assertEqual(len(response.data["comments"]), len(
            Comment.objects.filter(post_id='de305d54-75b4-431b-adb2-eb6b9e546012')))
        # Test that the most recent public post is the top result in the posts list
        self.assertEqual(response.data["comments"][0]
                         ["comment"], "This is the first comment")
        # Test that each element of a given content is equal to what we inputted
        self.assertEqual(response.data["comments"]
                         [0]["id"], self.comment1_id_string)
        self.assertEqual(response.data["comments"]
                         [0]["published"], self.comment1_published.strftime('%Y-%m-%dT%H:%M:%S%z'))
        self.assertEqual(response.data["comments"][0]
                         ["contentType"], self.comment1_contentType)
        self.assertEqual(response.data["comments"]
                         [0]["author"]["id"], self.testAuthor.id)

    def test_get_list_pagination(self):
        url = '/api/posts/de305d54-75b4-431b-adb2-eb6b9e546012/comments?size=1'
        response = self.client.get(url, format='json')
        # Test for response properly sent
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that we have retrieved one post
        self.assertEqual(len(response.data["comments"]), 1)
        self.assertTrue("&page=1" in response.data["next"])
        self.assertFalse("previous" in response.data.keys())

        # Get the next page, then test for the opposite
        url = '/api/posts/de305d54-75b4-431b-adb2-eb6b9e546012/comments?size=1&page=1'
        response = self.client.get(url, format='json')
        # Test for response properly sent
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test that we have retrieved one post
        self.assertEqual(len(response.data["comments"]), 1)
        # Test that we have a link to the next page, but not one to the previous page
        self.assertTrue("&page=0" in response.data["previous"])
        self.assertFalse("next" in response.data.keys())

    def test_post_valid_comment(self):
        comment_id_string = self.comment1_id_string[:-1] + '2'
        post_data = {
            "query": "addComment",
            "post": "http://whereitcamefrom.com/posts/zzzzz",
            "comment": {
                    "author": {
                        "id": self.testAuthor.id,
                        "host": self.testAuthor.host,
                        "displayName": self.testAuthor.displayName,
                        "url": self.testAuthor.url,
                        "github": self.testAuthor.github
                    },
                "comment": "Sick Olde English",
                "contentType": "text/markdown",
                "published": timezone.now(),
                "id": comment_id_string
            }
        }
        url = '/api/posts/de305d54-75b4-431b-adb2-eb6b9e546012/comments'
        response = self.client.post(url, post_data, format='json')
        # Test to ensure that this comment has been inserted
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Test that this new comment has entered the database
        self.assertEqual(Comment.objects.filter(
            id=comment_id_string).count(), 1)

    def test_post_comment_to_existing_uri(self):
        # This should fail
        comment_id_string = self.comment1_id_string
        post_data = {
            "query": "addComment",
            "post": "http://whereitcamefrom.com/posts/zzzzz",
            "comment": {
                    "author": {
                        "id": self.testAuthor.id,
                        "host": self.testAuthor.host,
                        "displayName": self.testAuthor.displayName,
                        "url": self.testAuthor.url,
                        "github": self.testAuthor.github
                    },
                "comment": "Sick Olde English",
                "contentType": "text/markdown",
                "published": timezone.now(),
                "id": comment_id_string
            }
        }
        url = '/api/posts/de305d54-75b4-431b-adb2-eb6b9e546012/comments'
        response = self.client.post(url, post_data, format='json')
        # Test to ensure that comment has been rejected
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_comment_invalid(self):
        # Suppose we post a comment without a comment in it
        comment_id_string = self.comment1_id_string[:-1] + '3'
        post_data = {
            "query": "addComment",
            "post": "http://whereitcamefrom.com/posts/zzzzz",
            "comment": {
                    "author": {
                        "id": self.testAuthor.id,
                        "host": self.testAuthor.host,
                        "displayName": self.testAuthor.displayName,
                        "url": self.testAuthor.url,
                        "github": self.testAuthor.github
                    },
                "contentType": "text/markdown",
                "published": timezone.now(),
                "id": comment_id_string
            }
        }
        url = '/api/posts/de305d54-75b4-431b-adb2-eb6b9e546012/comments'
        response = self.client.post(url, post_data, format='json')
        # Test to ensure that comment has been rejected
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthUserPosts(APITestCase):

    def setUp(self):
        # We will create two authors, and a few different kinds of posts.
        self.author1 = Author.objects.create(id='http://testserver.com/author/' + str(uuid.uuid4().hex), host="http://google.com", url="http://url.com",
                                             displayName="Author1", github="http://github.com/what", email="email1@mail.com", password="foo")
        self.author2 = Author.objects.create(id='http://testserver.com/author/' + str(uuid.uuid4().hex),
                                             displayName="Author2", first_name="Author", last_name="Two", email="email@mailtoot.com")
        self.author3 = Author.objects.create(id='http://testserver.com/author/' + str(uuid.uuid4().hex), host="http://google.com", url="http://url.com",
                                             displayName="Author3", github="http://github.com/what", email="email3@mail.com", password="foo")
        # We will also make another author who is from a foreign server.
        self.foreignAuthor = Author.objects.create(
            id="http://foreignsite.com/author/" + str(uuid.uuid4().hex), host="http://foreignsite.com", url="http://foreignsite.com", displayName="ForeignAuthor", github="", email="wahtever@email.com")
        # And we also make a Node with which to authenticate this author
        self.node = Node.objects.create(hostname="http://foreignsite.com",
                                        api_url="http://foreignsite.com", server_username="node", server_password="node")
        self.node_author = Author.objects.get(displayName="node")
        # We will make some friends here:
        # Author 1 will be friends with Author 2
        # Author 2 will be friends with Author 3
        Friend.objects.add_friend(self.author1, self.author2)
        Friend.objects.add_friend(self.author2, self.author3)

        # First post will be a public post written by author 1
        self.post1 = Post.objects.create(id=uuid.uuid4().hex, title="First Post", source=settings.FORMATTED_HOST_NAME,
                                         origin=settings.FORMATTED_HOST_NAME, description="This is the first post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2019, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PUBLIC", visibleTo="", unlisted=False)

        # Second post will be a private post written by author 1, shared with author 2 and the foreign author
        self.post2 = Post.objects.create(id=uuid.uuid4().hex, title="Second Post", source=settings.FORMATTED_HOST_NAME,
                                         origin=settings.FORMATTED_HOST_NAME, description="This is the second post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2018, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PRIVATE", visibleTo=str(self.author2.id) + ',' + str(self.foreignAuthor.id), unlisted=False)

        # Third post will be a public post written by author 2
        self.post3 = Post.objects.create(id=uuid.uuid4().hex, title="Third Post", source=settings.FORMATTED_HOST_NAME,
                                         origin="http://thirdpost.com/origin", description="This is the third post",
                                         author=self.author2, categories="", published=datetime.datetime(
            2017, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PUBLIC", visibleTo="", unlisted=False)

        # Fourth post will be a private post written by author 1, but NOT shared with author 2
        self.post4 = Post.objects.create(id=uuid.uuid4().hex, title="Fourth Post", source=settings.FORMATTED_HOST_NAME,
                                         origin="http://fourthpost.com/origin", description="This is the fourth post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2016, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PRIVATE", visibleTo="", unlisted=False)

        # Fifth post will be a post set to serveronly visibility by author 1. Only authors 1 and 2 should be able to see it.
        self.post5 = Post.objects.create(id=uuid.uuid4().hex, title="Fifth Post", source=settings.FORMATTED_HOST_NAME,
                                         origin="http://fourthpost.com/origin", description="This is the fourth post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2016, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="SERVERONLY", visibleTo="", unlisted=False)

        # Sixth post will be a post set to friend-only visibility by author1. Author 1 and 2 should be able to see it.
        self.post6 = Post.objects.create(id=uuid.uuid4().hex, title="Sixth Post", source=settings.FORMATTED_HOST_NAME,
                                         origin="http://fourthpost.com/origin", description="This is the fourth post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2016, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="FRIENDS", visibleTo="", unlisted=False)
        # Seventh post will be a FOAF post by author1. Everyone should be able to see it.
        self.post7 = Post.objects.create(id=uuid.uuid4().hex, title="Seventh Post", source=settings.FORMATTED_HOST_NAME,
                                         origin="http://fourthpost.com/origin", description="This is the fourth post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2016, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="FOAF", visibleTo="", unlisted=False)

    def test_get_list_as_user(self):
        url = reverse('auth-posts')
        response = self.client.get(url, format='json')
        # Without authenticating, we should be able to retrieve 1 post
        self.assertEqual(len(response.data["posts"]), 1)
        # We log in as author1
        self.client.force_authenticate(user=self.author1)
        response = self.client.get(url, format='json')
        # This user should be able to retrieve all posts
        self.assertEqual(len(response.data["posts"]), 7)
        # We log in as author2
        self.client.force_authenticate(user=self.author2)
        response = self.client.get(url, format='json')
        # They should be able to retrieve 6 posts
        self.assertEqual(len(response.data["posts"]), 6)
        # We log in as author3
        self.client.force_authenticate(user=self.author3)
        response = self.client.get(url, format='json')
        # They should be able to retrieve 3 posts
        self.assertEqual(len(response.data["posts"]), 3)

    def test_get_list_as_node(self):
        url = reverse('auth-posts')
        self.client.force_authenticate(user=self.node_author)
        response = self.client.get(url, format='json')
        # They should be able to see posts that originated from our server.
        self.assertEqual(len(response.data["posts"]), 2)


class AuthorPosts(APITestCase):

    def setUp(self):
        # We will create two authors, and a few different kinds of posts.
        self.author2 = Author.objects.create(id='http://testserver.com/author/' + str(uuid.uuid4().hex),
                                             displayName="Author2", first_name="Author", last_name="Two", email="email@mailtoot.com")
        self.author1 = Author.objects.create(id='http://testserver.com/author/' + str(uuid.uuid4().hex), host="http://google.com", url="http://url.com",
                                             displayName="Author1", github="http://github.com/what", email="email1@mail.com", password="foo")
        # We will also make another author who is from a foreign server.
        self.foreignAuthor = Author.objects.create(
            id="http://foreignsite.com/author/" + str(uuid.uuid4().hex), host="http://foreignsite.com", url="http://foreignsite.com", displayName="ForeignAuthor", github="", email="wahtever@email.com")
        # And we also make a Node with which to authenticate this author
        self.node = Node.objects.create(hostname="http://foreignsite.com",
                                        api_url="http://foreignsite.com", server_username="node", server_password="node")
        self.node_author = Author.objects.get(displayName="node")
        #  We will make them friends.
        Friend.objects.add_friend(self.author1, self.author2)
        # First post will be a public post written by author 1
        self.post1 = Post.objects.create(id=uuid.uuid4().hex, title="First Post", source=settings.FORMATTED_HOST_NAME,
                                         origin="http://firstpost.com/origin", description="This is the first post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2019, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PUBLIC", visibleTo="", unlisted=False)

        # Second post will be a private post written by author 1, shared with author 2 and the foreign author
        self.post2 = Post.objects.create(id=uuid.uuid4().hex, title="Second Post", source=settings.FORMATTED_HOST_NAME,
                                         origin="http://secondpost.com/origin", description="This is the second post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2018, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PRIVATE", visibleTo=str(self.author2.id)+','+str(self.foreignAuthor.id), unlisted=False)

        # Third post will be a public post written by author 2
        self.post3 = Post.objects.create(id=uuid.uuid4().hex, title="Third Post", source=settings.FORMATTED_HOST_NAME,
                                         origin="http://thirdpost.com/origin", description="This is the third post",
                                         author=self.author2, categories="", published=datetime.datetime(
            2017, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PUBLIC", visibleTo="", unlisted=False)

        # Fourth post will be a private post written by author 1, but NOT shared with author 2
        self.post4 = Post.objects.create(id=uuid.uuid4().hex, title="Fourth Post", source=settings.FORMATTED_HOST_NAME,
                                         origin="http://fourthpost.com/origin", description="This is the fourth post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2016, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PRIVATE", visibleTo="", unlisted=False)
        # Fifth post will be a post written by author1 visible only to friends on the server
        self.post5 = Post.objects.create(id=uuid.uuid4().hex, title="Fifth Post", source=settings.FORMATTED_HOST_NAME,
                                         origin="http://fourthpost.com/origin", description="This is the fourth post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2016, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="SERVERONLY", visibleTo="", unlisted=False)
        # Sixth post will be written by author1 visible only to friends
        self.post6 = Post.objects.create(id=uuid.uuid4().hex, title="Sixth Post", source=settings.FORMATTED_HOST_NAME,
                                         origin="http://fourthpost.com/origin", description="This is the fourth post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2016, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="FRIENDS", visibleTo="", unlisted=False)
        # Seventh post will be written by author1 visible only to FOAF
        self.post7 = Post.objects.create(id=uuid.uuid4().hex, title="Seventh Post", source=settings.FORMATTED_HOST_NAME,
                                         origin="http://fourthpost.com/origin", description="This is the fourth post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2016, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="FOAF", visibleTo="", unlisted=False)

    def test_get_list(self):
        author_uuid_blurb = self.author1.id[29:]
        url = '/api/author/' + author_uuid_blurb + '/posts'
        response = self.client.get(url, format='json')
        # Without authenticating, we should be able to retrieve 1 post
        self.assertEqual(len(response.data["posts"]), 1)
        # We log in as author2
        self.client.force_authenticate(user=self.author2)
        response = self.client.get(url, format='json')
        # We should be seeing 5 posts
        self.assertEqual(len(response.data["posts"]), 5)
        # We log in as author1
        self.client.force_authenticate(user=self.author1)
        response = self.client.get(url, format='json')
        # We should be seeing 6 posts
        self.assertEqual(len(response.data["posts"]), 6)
        # If we log in as the foreign author, we should be able to retrieve 2 posts
        self.client.force_authenticate(user=self.node_author)
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data["posts"]), 2)


class AuthorFriendsList(APITestCase):

    def setUp(self):
        # We will create three authors.
        self.author1 = Author.objects.create(id='http://testserver.com/author/' + str(uuid.uuid4().hex), host="http://google.com", url="http://url.com",
                                             displayName="Author1", github="http://github.com/what", email="email1@mail.com")
        self.author2 = Author.objects.create(id='http://testserver.com/author/' + str(uuid.uuid4().hex),
                                             displayName="Author2", first_name="Author", last_name="Two", email="email@mailtoot.com")
        self.author3 = Author.objects.create(id='http://testserver.com/author/' + str(uuid.uuid4().hex), host="http://google.com", url="http://url.com",
                                             displayName="Author3", github="http://github.com/what", email="email3@mail.com")

        # We will set author1 to be friends with author2, and author3 to be friends with author1
        Friend.objects.add_friend(self.author1, self.author2)
        Friend.objects.add_friend(self.author1, self.author3)

    def test_get(self):
        url = '/api/author/' + self.author1.id[29:] + '/friends'
        response = self.client.get(url, format='json')
        # We should get a response listing one author
        self.assertEqual(len(response.data["authors"]), 2)
        self.assertTrue(self.author2.id in response.data["authors"])
        # We should get an equivalent response by requesting the friends of author2
        url = '/api/author/' + self.author2.id[29:] + '/friends'
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data["authors"]), 1)
        self.assertTrue(self.author1.id in response.data["authors"])
        # We should get no results if we remove the friend
        self.assertTrue(Friend.objects.are_friends(self.author2, self.author1))
        Friend.objects.remove_friend(self.author1, self.author2)
        response = self.client.get(url, format='json')
        self.assertEqual(len(response.data["authors"]), 0)

    def test_valid_post(self):
        url = '/api/author/' + self.author1.id[29:] + '/friends'
        post_body = {
            "query": "friends",
            "author": self.author1.id,
            "authors": [
                self.author2.id
            ]
        }
        response = self.client.post(url, post_body, format='json')
        # We should only get one matching author. It should be author2.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["authors"]), 1)
        self.assertTrue(self.author2.id in response.data["authors"])
        self.assertEqual(len(Friend.objects.get_friends(self.author1)), 2)

    def test_invalid_post(self):
        url = '/api/author/' + self.author1.id[29:] + '/friends'
        post_body = {
            "query": "friends",
            "author": self.author1.id,
        }
        response = self.client.post(url, post_body, format='json')
        # We should receive a 400 error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AreAuthorsFriends(APITestCase):
    def setUp(self):
        # We will create three authors.
        self.author1 = Author.objects.create(id='http://testserver.com/author/' + str(uuid.uuid4().hex), host="http://google.com", url="http://url.com",
                                             displayName="Author1", github="http://github.com/what", email="email1@mail.com")
        self.author2 = Author.objects.create(id='http://testserver.com/author/' + str(uuid.uuid4().hex),
                                             displayName="Author2", first_name="Author", last_name="Two", email="email@mailtoot.com")
        self.author3 = Author.objects.create(id='http://testserver.com/author/' + str(uuid.uuid4().hex), host="http://google.com", url="http://url.com",
                                             displayName="Author3", github="http://github.com/what", email="email3@mail.com")
        # We will make author 1 and 2 friends.
        Friend.objects.add_friend(self.author1, self.author2)

    def test_get(self):
        # We query for authors 1 and 2. They should be friends.
        safe_author2 = urllib.parse.quote(
            self.author2.id[7:], safe='~()*!.\'')
        url = '/api/author/' + \
            self.author1.id[29:] + '/friends/' + safe_author2
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.author1.id in response.data["authors"])
        self.assertTrue(self.author2.id in response.data["authors"])
        self.assertTrue(response.data["friends"])
        # We test for authors 1 and 3. They are not friends
        safe_author3 = urllib.parse.quote(
            self.author3.id[7:], safe='~()*!.\'')
        url = '/api/author/' + \
            self.author1.id[29:] + '/friends/' + safe_author3
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.author1.id in response.data["authors"])
        self.assertTrue(self.author3.id in response.data["authors"])
        self.assertFalse(response.data["friends"])

    def test_author_not_found(self):
        # If an author is not found we should receive a 404
        safe_fakeauthor = urllib.parse.quote(
            'fakeservice.com/author/fakeuser/', safe='~() *!.\'')
        url = '/api/author/' + \
            self.author1.id[29:] + '/friends/' + safe_fakeauthor
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class FriendRequest(APITestCase):
    def setUp(self):
        # We will create two authors.
        self.author1 = Author.objects.create(id='http://testserver.com/author/' + str(uuid.uuid4().hex), host="http://google.com", url="http://url.com",
                                             displayName="Author1", github="http://github.com/what", email="email1@mail.com")
        self.author2 = Author.objects.create(id='http://testserver.com/author/' + str(uuid.uuid4().hex),
                                             displayName="Author2", first_name="Author", last_name="Two", email="email@mailtoot.com")
        # We will also make another author who is from a foreign server.
        self.foreignAuthor = Author.objects.create(
            id="http://foreignsite.com/author/" + str(uuid.uuid4().hex), host="http://foreignsite.com", url="http://foreignsite.com", displayName="ForeignAuthor", github="", email="wahtever@email.com")
        # And we also make a Node with which to authenticate this author
        self.node = Node.objects.create(hostname="http://foreignsite.com",
                                        api_url="http://foreignsite.com", server_username="node", server_password="node")
        self.node_author = Author.objects.get(displayName="node")

    def test_post_valid_format_as_user(self):
        # We are authenticating as a user in our database.
        # Since author1 is the one sending it, we should authenticate as them.
        self.client.force_authenticate(user=self.author1)
        post_body = {
            "query": "friendrequest",
            "author": {
                "id": self.author1.id,
                "host": self.author1.host,
                "displayName": self.author1.displayName,
                "url": self.author1.url
            },
            "friend": {
                "id": self.author2.id,
                "host": self.author2.host,
                "displayName": self.author2.displayName,
                "url": self.author2.url
            }
        }
        url = '/api/friendrequest'
        response = self.client.post(url, post_body, format='json')
        # Assert we got a 200 OK, and that it was a success
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        # Assert that it is in the db
        self.assertTrue(Follower.objects.is_following(
            self.author1, self.author2))
        # if we send it again, it should return a 400
        response = self.client.post(url, post_body, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertTrue(response.data["message"].find(
            "has already sent a friend request to"))
        # If we send a message the opposite way, they should now be friends
        post_body = post_body = {
            "query": "friendrequest",
            "author": {
                "id": self.author2.id,
                "host": self.author2.host,
                "displayName": self.author2.displayName,
                "url": self.author2.url
            },
            "friend": {
                "id": self.author1.id,
                "host": self.author1.host,
                "displayName": self.author1.displayName,
                "url": self.author1.url
            }
        }
        self.client.force_authenticate(user=self.author2)
        response = self.client.post(url, post_body, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Friend.objects.are_friends(self.author1, self.author2))
        self.assertTrue(response.data["message"].find(
            "are now friends"))
        # If they are already friends, we should receive a 400
        response = self.client.post(url, post_body, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertTrue(response.data["message"].find(
            "is already friends with"))

    def test_valid_format_as_node(self):
        self.client.force_authenticate(user=self.node_author)
        post_body = {
            "query": "friendrequest",
            "author": {
                "id": self.foreignAuthor.id,
                "host": self.foreignAuthor.host,
                "displayName": self.foreignAuthor.displayName,
                "url": self.foreignAuthor.url
            },
            "friend": {
                "id": self.author2.id,
                "host": self.author2.host,
                "displayName": self.author2.displayName,
                "url": self.author2.url
            }
        }
        url = '/api/friendrequest'
        response = self.client.post(url, post_body, format='json')
        # Assert we got a 200 OK, and that it was a success
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        # Assert that it is in the db
        self.assertTrue(Follower.objects.is_following(
            self.foreignAuthor, self.author2))
        # if we send it again, it should return a 400
        response = self.client.post(url, post_body, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertTrue(response.data["message"].find(
            "has already sent a friend request to"))
        # If we make them friends, it should return a 400
        Friend.objects.add_friend(self.foreignAuthor, self.author2)
        response = self.client.post(url, post_body, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertTrue(response.data["message"].find(
            "is already friends with"))

    def test_post_invalid_format(self):
        self.client.force_authenticate(user=self.author1)
        post_body = {
            "query": "friendrequest",
            "author": {
                "id": self.author1.id,
                "host": self.author1.host,
                "displayName": self.author1.displayName,
                "url": self.author1.url
            },
            "fiend": {
                "id": self.author2.id,
                "host": self.author2.host,
                "displayName": self.author2.displayName,
                "url": self.author2.url
            }
        }
        url = '/api/friendrequest'
        response = self.client.post(url, post_body, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertTrue(response.data["message"].find(
            "incorrectly formatted"))
        # Now we send it with a friend who does not exist
        post_body = {
            "query": "friendrequest",
            "author": {
                "id": "hey",
                "host": "whaddup",
                "displayName": "sup",
                "url": "url.com"
            },
            "friend": {
                "id": self.author2.id,
                "host": self.author2.host,
                "displayName": self.author2.displayName,
                "url": self.author2.url
            }
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertTrue(response.data["message"].find(
            "incorrectly formatted"))


def test_post_valid_format_incorrect_user(self):
    # We are authenticating as a user in our database, but not the right one
    # Since author1 is the one sending it, we should authenticate as them.
    self.client.force_authenticate(user=self.author2)
    post_body = {
        "query": "friendrequest",
        "author": {
            "id": self.author1.id,
            "host": self.author1.host,
            "displayName": self.author1.displayName,
            "url": self.author1.url
        },
        "friend": {
            "id": self.author2.id,
            "host": self.author2.host,
            "displayName": self.author2.displayName,
            "url": self.author2.url
        }
    }
    url = '/api/friendrequest'
    response = self.client.post(url, post_body, format='json')
    # Assert we got a 401, since we cannot do this action
    self.assertEquals(response.status_code, status.HTTP_401_UNAUTHORIZED)


def test_no_authentication(self):
    post_body = {
        "query": "friendrequest",
        "author": {
            "id": self.author1.id,
            "host": self.author1.host,
            "displayName": self.author1.displayName,
            "url": self.author1.url
        },
        "friend": {
            "id": self.author2.id,
            "host": self.author2.host,
            "displayName": self.author2.displayName,
            "url": self.author2.url
        }
    }
    url = '/api/friendrequest'
    response = self.client.post(url, post_body, format='json')
    # Assert we got a 401, since we cannot do this action without authentication
    self.assertEquals(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthorDetail(APITestCase):

    def setUp(self):
        # We create an author
        self.author1 = Author.objects.create(id='http://testserver.com/author/' + str(uuid.uuid4().hex), host="http://google.com", url="http://url.com",
                                             displayName="Author1", github="http://github.com/what", email="email1@mail.com")

    def test_get_valid_uuid(self):
        url = '/api/author/' + self.author1.id[29:]
        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data["id"], self.author1.id)
        self.assertEquals(
            response.data["displayName"], self.author1.displayName)
        self.assertEquals(response.data["email"], self.author1.email)
        self.assertEquals(response.data["url"], self.author1.url)
        self.assertEquals(response.data["host"], self.author1.host)
        self.assertEquals(response.data
                          ["github"], self.author1.github)

    def test_get_invalid_uuid(self):
        url = '/api/author/123456'
        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_404_NOT_FOUND)
