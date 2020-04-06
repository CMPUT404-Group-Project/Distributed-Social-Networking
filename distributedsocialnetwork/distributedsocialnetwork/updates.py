# Thanks to user Tanner Swett's answer https://stackoverflow.com/a/60244694
# From Zeokav's question https://stackoverflow.com/q/44896618


from schedule import Scheduler
import threading
import time
from post.retrieval import get_public_posts, get_detailed_post
from author.retrieval import get_detailed_author, get_visible_posts, get_github_activity
from friend.retrieval import update_friends_list
from author.models import Author
from post.models import Post
from django.conf import settings


def get_all_public_posts():
    get_public_posts()


def get_all_visible_posts():
    print(">>>>>> Getting Visible Posts")
    # get_visible_posts will pull in all visible posts for all authors, but we need to supply one author id (doesn't matter who)
    if len(Author.objects.filter(host=settings.FORMATTED_HOST_NAME)) != 0:
        author = Author.objects.filter(host=settings.FORMATTED_HOST_NAME)[0]
        get_visible_posts(author.id)
    print('<<<<<< Visible Posts Pull Complete')


def get_all_github_activity():
    # Get the github activity for all our local authors.
    print(">>>>>> Pulling GitHub Activity")
    for author in Author.objects.filter(host=settings.FORMATTED_HOST_NAME):
        get_github_activity(author_id=author.id)
    print('<<<<<< GitHub Pull Complete')


def update_detailed_posts():
    print(">>>>>> Updating Foreign Posts")
    for post in Post.objects.all().exclude(origin__icontains=settings.FORMATTED_HOST_NAME):
        get_detailed_post(post.id)
    print('<<<<<< Foreign Post Update Complete')


def update_all_foreign_authors():
    print(">>>>>> Updating Foreign Authors")
    for author in Author.objects.filter(is_node=False).exclude(host=settings.FORMATTED_HOST_NAME):
        print(author.id)
        update_friends_list(author.id)
        get_detailed_author(author.id)
    print('<<<<<< Foreign Author Update Complete')


def get_updates():
    update_all_foreign_authors()
    get_all_github_activity()
    get_all_visible_posts()
    update_detailed_posts()
    # get_all_public_posts()
    # print("Updating Foreign Authors\n======")


def run_continuously(self, interval=1):
    """Continuously run, while executing pending jobs at each elapsed
    time interval.
    @return cease_continuous_run: threading.Event which can be set to
    cease continuous run.
    Please note that it is *intended behavior that run_continuously()
    does not run missed jobs*. For example, if you've registered a job
    that should run every minute and you set a continuous run interval
    of one hour then your job won't be run 60 times at each interval but
    only once.
    """

    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):

        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                self.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.setDaemon(True)
    continuous_thread.start()
    return cease_continuous_run


Scheduler.run_continuously = run_continuously


def all_updates_scheduler():
    # Running them all in one thread again
    scheduler = Scheduler()
    scheduler.every(30).seconds.do(get_updates)
    scheduler.run_continuously()


def foreignauthors_scheduler():
    scheduler = Scheduler()
    scheduler.every(30).seconds.do(update_all_foreign_authors)
    scheduler.run_continuously()


def github_scheduler():
    scheduler = Scheduler()
    scheduler.every(30).seconds.do(get_all_github_activity)
    scheduler.run_continuously()


def visibleposts_scheduler():
    scheduler = Scheduler()
    scheduler.every(30).seconds.do(get_all_visible_posts)
    scheduler.run_continuously()


def detailedposts_scheduler():
    scheduler = Scheduler()
    scheduler.every(30).seconds.do(update_detailed_posts)
    scheduler.run_continuously()
