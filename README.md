# Distributed Social Networking

## Project Overview

### Description
This project is a more manageable implementation of [Diaspora*](https://diasporafoundation.org/), where each team will create a blogging website that allows users to create and share post with other users on the same site. Additionally, each site can connect, sharing users and post between sites.

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
```
Collaborator 1
Collaborator 2
...
```

### External Source Code
```
External Source 1
External Source 2
...
```

### Working With Teams
```
CMPUT404W20T00
CMPUT404W20T00
```

### Directory Layout
```
Distributed-Social-Networking
|
├── distributedsocialnetwork/   (Django Files)
|
└── docs/                       (General Files)
```

Manual Copy/Paste or use `tree -d -L [depth]`
```
├──
|   └──
|   |   ├── 
```

## Instructions
### Setup
**Make sure *libpq-dev* and *python-dev* is installed**

*dependencies for psycopg2 and Django-Heroku*
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



### Run
**Create migrations and migrate**
```
$ cd distributedsocialnetwork
$ ./manage makemigrations [app]
$ ./manage migrate
```

**Run Django server**
```
$ ./manage.py runserver
```

## Original Contributors and Licensing
Generally everything is LICENSED under the Apache 2.0 license by [Abram Hindle](https://github.com/abramhindle) and modified to include members of our team

All text is licensed under the [CC-BY-SA 4.0](http://creativecommons.org/licenses/by-sa/4.0/deed.en_US) license

Original *'docs/example-article.json'*, *'docs/project.org'*, and *'docs/swagger_doc.yml'* can be found at [abramhindle's repo](https://github.com/abramhindle/CMPUT404-project-socialdistribution)

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
