# django-sqltemplate
Database query tool for Django, based on SQL templates

## Introduction

SQL is a great and poweruful DSL, which is easeier in maintenance 
when you're working on complext queries (i.e. reporting queries).
But the main problem of raw SQL is a commonly used "spaghetti" anti-pattern, 
when you're embedding/building SQLs directly in your code.

The solution comes from templating SQLs idea and `django-sqltemplate` 
is a simple implementation of it.

## Quickstart

Install package:

```pip install django-sqltemplate```

Make `sqltemplates` directory in your Django app (your app must be added to `INSTALLED_APPS`):

```mkdir <django-project>/<my-app>/sqltemplates```

Put `hello.sql` template in `sqltemplates` directory:

hello.sql (assuming sqlite syntax)
```sql
select 'Hello ' || :name as message;
```

Execute the query:

```python
>>> import sqltemplate
>>> hello = sqltemplate.get('hello.sql')
>>> print hello(name='Marcin').values()
[{'message': u'Hello Marcin'}]
```

If query returns just one row (as in example above) you may read result directly using `.scalar()` method:

```python
>>> print hello(name='Marcin').scalar()
Hello Marcin
```

To fetch results as a list of dictionaries use `.values()` method:

```python
>>> print hello(name='Marcin').values()
[{'message': u'Hello Marcin'}]
```

To fetch results as a list of tuples use `.values_list()` method:

```python
>>> print hello(name='Marcin').values_list()
[(u'Hello Marcin',)]
```

To fetch results as iterator over tuples use `.iterator()` method:

```python
>>> print hello(name='Marcin').iterator()
<generator object _fetch at 0x7f8abd202870>
```

To fetch results as iterator over dictionaries use `.dictiterator()` method:

```python
>>> print hello(name='Marcin').dictiterator()
<generator object _fetch at 0x7f8abd202820>
```
