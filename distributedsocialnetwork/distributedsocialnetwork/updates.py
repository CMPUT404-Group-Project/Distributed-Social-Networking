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
    # get_visible_posts will pull in all visible posts for all authors, but we need to supply one author id (doesn't matter who)
    author = Author.objects.filter(host=settings.FORMATTED_HOST_NAME)[0]
    get_visible_posts(author.id)

def get_all_github_activity():
    # Get the github activity for all our local authors.
    for author in Author.objects.filter(host=settings.FORMATTED_HOST_NAME):
        get_github_activity(author_id=author.id)

def update_detailed_posts():
    for post in Post.objects.all().exclude(origin__icontains=settings.FORMATTED_HOST_NAME):
        get_detailed_post(post.id)


def update_all_foreign_authors():
    for author in Author.objects.all().exclude(host=settings.FORMATTED_HOST_NAME):
        get_detailed_author(author.id)
        update_friends_list(author.id)


def get_updates():
    get_all_github_activity()
    # print("Getting Visible Posts\n======")
    get_all_visible_posts()
    update_detailed_posts()
    # print("Getting Public Posts\n======")
    get_all_public_posts()
    # print("Updating Foreign Authors\n======")
    update_all_foreign_authors()
    

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


def start_scheduler():
    scheduler = Scheduler()
    scheduler.every(30).seconds.do(get_updates)
    scheduler.run_continuously()
