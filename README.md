# Distributed Social Networking (DSN-404)

## Project Overview

### Description

This project is a more manageable implementation of [Diaspora\*](https://diasporafoundation.org/), where each team will create a blogging website that allows users to create and share post with other users on the same site. Additionally, each site can connect, sharing users and post between sites.

### CMPUT404W20T03 Members

```
Anders Johnson
Andrew Smith
Daniel Dick
Joseph Potentier
Justin Liew
Ken Li
```

### Collaborators

`N/A`

### External Source Code

`N/A`

### Working With Teams

```
CMPUT404W20T00
CMPUT404W20T00
```

### Directory Layout

```

Distributed-Social-Networking
│   ├── api                       (API functionality)
│   ├── author                    (Custom User (author) Model)
│   ├── bootstrap                 (Custom Bootstrap CSS)
│   ├── distributedsocialnetwork  (Django Files)
│   ├── friend                    (Friend Model)
│   ├── post                      (Post Model)
│   ├── staticfiles               (Django Static Files)
│   └── templates                 (HTML Templates Files)
├── docs
```

Generate Directory Layout `tree -d -L [depth]`

## Instructions

### Setup

**Make sure _libpq-dev_ and _python-dev_ is installed**

_dependencies for psycopg2 and Django-Heroku_

```
$ sudo apt-get install libpq-dev python-dev
```

**Initialize a virutal environment**

```
$ virtualenv --python=python3 venv
```

**Activate the virtual environment**

```
$ source venv/bin/activate
```

**Install packages from requirements**

```
$ pip install -r requirements.txt
```

### Running Locally

**Create migrations and migrate**

```
$ cd distributedsocialnetwork
$ ./manage makemigrations [app]
$ ./manage migrate
```

**Compile w/ Sass**
If you are going to be editing any of the base scss files for fine tuning bootstrap styling you will need a sass compiler. Install one from this page(super easy): https://sass-lang.com/install

To theme bootstrap, this is a great reference: https://www.mugo.ca/Blog/How-to-customize-Bootstrap-4-using-Sass

From the base django folder:

```
sass ./bootstrap/scss/main.scss:bootstrap/css/bootstrap/bootstrap-override.css
```

**Run Django server**

```

$ ./manage.py runserver

```

### Running on Heroku

Link: https://dsnfof.herokuapp.com/

**Create superuser**

```

$ heroku run --app dsnfof python distributedsocialnetwork/manage.py createsuperuser

```

## Original Contributors and Licensing

Generally everything is LICENSED under the Apache 2.0 license by [Abram Hindle](https://github.com/abramhindle) and modified to include members of our team

All text is licensed under the [CC-BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/deed.en_US) license

Original _'docs/example-article.json'_, _'docs/project.org'_, and _'docs/swagger_doc.yml'_ can be found at [abramhindle's repo](https://github.com/abramhindle/CMPUT404-project-socialdistribution)

### Other Contributors

```

Abram Hindle
Ali Sajedi
Braedy Kuzma
Chris Pavlicek
Derek Dowling
Erin Torbiak
Karim Baaba
Kyle Richelhoff
Olexiy Berjanskiia

```
