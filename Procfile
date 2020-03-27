release: cd distributedsocialnetwork; python manage.py migrate; python manage.py test
web: gunicorn --pythonpath distributedsocialnetwork distributedsocialnetwork.wsgi
