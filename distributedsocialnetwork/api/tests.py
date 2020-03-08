from django.test import TestCase, Client
from rest_framework import status
from rest_framework.test import APITestCase, URLPatternsTestCase, force_authenticate, APIRequestFactory
from author.models import Author
from post.models import Post, Comment
from django.urls import include, path, reverse
import uuid
import datetime
import pytz
# Create your tests here.


class VisiblePosts(APITestCase):
    def setUp(self):

        self.testUserId = uuid.uuid4().hex
        self.testAuthor = Author.objects.create(id=self.testUserId, host="http://google.com", url="http://url.com",
                                                displayName="Testmaster", github="http://github.com/what")
        # Post 1
        self.post_id1 = uuid.uuid4().hex
        self.title1 = "Test1"
        self.source1 = 'http://testcase1.com'
        self.origin1 = 'http://testcase1.com/original'
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
        self.source2 = 'http://testcase2.com'
        self.origin2 = 'http://testcase2.com/original'
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
        self.source3 = 'http://testcase3.com'
        self.origin3 = 'http://testcase3.com/original'
        self.description3 = 'Description3'
        self.contentType3 = "text/plain"
        self.content3 = "Content of the first test case post"
        self.author3 = self.testAuthor
        self.categories3 = ""
        self.published3 = datetime.datetime.now()
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
                         'http://testserver' + url + response.data["posts"][0]["id"] + '/comments')
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
        self.testUserId = uuid.uuid4().hex
        self.testAuthor = Author.objects.create(id=self.testUserId, host="http://google.com", url="http://url.com",
                                                displayName="Testmaster", github="http://github.com/what")
        # Post 1
        self.post_id1_string = 'de305d54-75b4-431b-adb2-eb6b9e546013'
        self.post_id1 = uuid.UUID('de305d54-75b4-431b-adb2-eb6b9e546013')
        self.title1 = "Test1"
        self.source1 = 'http://testcase1.com'
        self.origin1 = 'http://testcase1.com/original'
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
        url = '/api/posts/' + self.post_id1_string + '/'
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
                         'http://testserver' + url + 'comments')

    def test_post_to_existing_uri(self):
        # This should fail
        url = '/api/posts/' + self.post_id1_string + '/'

        response = self.client.post(url, self.post_data, format='json')
        # Test to ensure that this post has not been inserted
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_to_new_uri(self):
        # This should succeed and return a 201 Created
        new_post_id = self.post_id1_string[:-1] + '4'
        url = '/api/posts/' + new_post_id + '/'
        response = self.client.post(url, self.post_data, format='json')
        # Test to ensure that this post has been inserted
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Test that this new post has entered the database
        self.assertEqual(Post.objects.filter(id=new_post_id).count(), 1)

    def test_post_invalid_format(self):
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
        url = '/api/posts/' + new_post_id + '/'
        response = self.client.post(url, invalid_post, format='json')
        # We don't have a title set, so it should fail to create the post
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_valid_format(self):
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
        url = '/api/posts/' + self.post_id1_string + '/'
        response = self.client.put(url, post_data, format='json')
        # Check that it responds with 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that it actually updated
        post = Post.objects.filter(id=self.post_id1)[0]
        self.assertEqual(post.title, "This is the updated title!")

    def test_put_invalid_format(self):
        post_data = {
            "query": "addPost",
            "post": {
                "author": {
                    "id": "foo",
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
        url = '/api/posts/' + self.post_id1_string + '/'
        response = self.client.put(url, post_data, format='json')
        # We don't have a title set, so it should fail to create the post
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Let's ensure it didn't update the post
        post = Post.objects.filter(id=self.post_id1)[0]
        self.assertNotEqual(post.title, "This is the updated title!")


class CommentList(APITestCase):
    def setUp(self):
        self.testUserId = uuid.uuid4().hex
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
                "published": "2015-03-09T13:07:04+00:00",
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
                "published": "2015-03-09T13:07:04+00:00",
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
                "published": "2015-03-09T13:07:04+00:00",
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
        self.author2 = Author.objects.create(id=str(uuid.uuid4().hex),
                                             displayName="Author2", first_name="Author", last_name="Two", email="email@mailtoot.com")
        self.author1 = Author.objects.create(id=str(uuid.uuid4().hex), host="http://google.com", url="http://url.com",
                                             displayName="Author1", github="http://github.com/what", email="email1@mail.com", password="foo")

        # First post will be a public post written by author 1
        self.post1 = Post.objects.create(id=uuid.uuid4().hex, title="First Post", source="http:firstpost.com",
                                         origin="http://firstpost.com/origin", description="This is the first post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2019, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PUBLIC", visibleTo="", unlisted=False)

        # Second post will be a private post written by author 1, shared with author 2
        self.post2 = Post.objects.create(id=uuid.uuid4().hex, title="Second Post", source="http:secondpost.com",
                                         origin="http://secondpost.com/origin", description="This is the second post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2018, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PRIVATE", visibleTo=self.author2.id, unlisted=False)

        # Third post will be a public post written by author 2
        self.post3 = Post.objects.create(id=uuid.uuid4().hex, title="Third Post", source="http:thirdpost.com",
                                         origin="http://thirdpost.com/origin", description="This is the third post",
                                         author=self.author2, categories="", published=datetime.datetime(
            2017, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PUBLIC", visibleTo="", unlisted=False)

        # Fourth post will be a private post written by author 1, but NOT shared with author 2
        self.post4 = Post.objects.create(id=uuid.uuid4().hex, title="Fourth Post", source="http:fourthpost.com",
                                         origin="http://fourthpost.com/origin", description="This is the fourth post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2016, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PRIVATE", visibleTo="", unlisted=False)

    def test_get_list(self):
        url = reverse('auth-posts')
        response = self.client.get(url, format='json')
        # Without authenticating, we should be able to retrieve 2 posts
        self.assertEqual(len(response.data["posts"]), 2)
        # We log in as author2
        self.client.force_authenticate(user=self.author2)
        response = self.client.get(url, format='json')
        # This user should be able to retrieve 3 posts
        self.assertEqual(len(response.data["posts"]), 3)


class AuthorPosts(APITestCase):

    def setUp(self):
        # We will create two authors, and a few different kinds of posts.
        self.author2 = Author.objects.create(id=str(uuid.uuid4().hex),
                                             displayName="Author2", first_name="Author", last_name="Two", email="email@mailtoot.com")
        self.author1 = Author.objects.create(id=str(uuid.uuid4().hex), host="http://google.com", url="http://url.com",
                                             displayName="Author1", github="http://github.com/what", email="email1@mail.com", password="foo")

        # First post will be a public post written by author 1
        self.post1 = Post.objects.create(id=uuid.uuid4().hex, title="First Post", source="http:firstpost.com",
                                         origin="http://firstpost.com/origin", description="This is the first post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2019, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PUBLIC", visibleTo="", unlisted=False)

        # Second post will be a private post written by author 1, shared with author 2
        self.post2 = Post.objects.create(id=uuid.uuid4().hex, title="Second Post", source="http:secondpost.com",
                                         origin="http://secondpost.com/origin", description="This is the second post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2018, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PRIVATE", visibleTo=self.author2.id, unlisted=False)

        # Third post will be a public post written by author 2
        self.post3 = Post.objects.create(id=uuid.uuid4().hex, title="Third Post", source="http:thirdpost.com",
                                         origin="http://thirdpost.com/origin", description="This is the third post",
                                         author=self.author2, categories="", published=datetime.datetime(
            2017, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PUBLIC", visibleTo="", unlisted=False)

        # Fourth post will be a private post written by author 1, but NOT shared with author 2
        self.post4 = Post.objects.create(id=uuid.uuid4().hex, title="Fourth Post", source="http:fourthpost.com",
                                         origin="http://fourthpost.com/origin", description="This is the fourth post",
                                         author=self.author1, categories="", published=datetime.datetime(
            2016, 1, 1, 1, 1, 1, tzinfo=pytz.UTC), visibility="PRIVATE", visibleTo="", unlisted=False)

    def test_get_list(self):
        url = '/api/author/' + self.author1.id + '/posts'
        print("url is", url)
        response = self.client.get(url, format='json')
        # Without authenticating, we should be able to retrieve 1 post
        self.assertEqual(len(response.data["posts"]), 1)
        # We log in as author2
        self.client.force_authenticate(user=self.author2)
        response = self.client.get(url, format='json')
        # We should be seeing 2 posts
        self.assertEqual(len(response.data["posts"]), 2)
        # We log in as author1
        self.client.force_authenticate(user=self.author1)
        response = self.client.get(url, format='json')
        # We should be seeing 3 posts
        self.assertEqual(len(response.data["posts"]), 3)
