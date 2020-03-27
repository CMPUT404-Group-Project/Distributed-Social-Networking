# Thanks to https://stackoverflow.com/a/60244694

from schedule import Scheduler
import threading
import time
from post.retrieval import get_public_posts, get_detailed_post
from author.retrieval import get_detailed_author, get_visible_posts
from friend.retrieval import update_friends_list
from author.models import Author


def get_all_public_posts():
    get_public_posts()


def print_foo():
    print("FOOOOOOOOO")


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
    # scheduler.every(30).seconds.do(get_public_posts)
    scheduler.every().second.do(print_foo)
    scheduler.run_continuously()
