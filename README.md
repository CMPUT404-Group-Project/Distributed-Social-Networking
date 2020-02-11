# Distributed Social Networking

## Project Overview

### Description
\[Insert Project Description\]

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
\[Collaborators\]

### External Source Code
\[External Source Code\]

### Other Teams
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
