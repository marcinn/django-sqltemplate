# django-sqltemplate
Database query tool for Django, based on SQL templates

## Development status

* Alpha
* API may be radically changed until first Beta release
* Not tested automatically yet
 
### Roadmap

* 0.6 - stable API
* 0.7 - automated tests, first Beta release
* 0.8,<1.0 - minor improvements without API changes, bugfixes
* 1.0 - first Stable release

## Introduction

SQL is a great and poweruful DSL, which is easeier in maintenance 
when you're working on complext queries (i.e. reporting queries).
But the main problem of raw SQL is a commonly used "spaghetti" anti-pattern, 
when you're embedding/building SQLs directly in your code.

The solution comes from templating SQLs idea and `django-sqltemplate` 
is a simple implementation of it.

## Quickstart

### Install the package

```pip install django-sqltemplate```

### Add application to the INSTALLED_APPS

```
    INSTALLED_APPS = [
       ...
       'djsqltemplate',
       ...
       ]
```

### Add SQL template(s)

Make `sqltemplates` directory in your Django app (your app must be added to
`INSTALLED_APPS`):

```mkdir <django-project>/<my-app>/sqltemplates```

Put `hello.sql` template in `sqltemplates` directory:

hello.sql (assuming sqlite syntax)
```sql
select 'Hello ' || :name as message
```

### Query the database

```python
>>> import djsqltemplate
>>> hello = djsqltemplate.get('hello.sql')
>>> print hello.values(name='Marcin')
[{'message': u'Hello Marcin'}]
```

If query returns just one row (as in example above) you may read result
directly using `.scalar()` method:

```python
>>> print hello.scalar(name='Marcin')
Hello Marcin
```

To fetch results as a list of dictionaries use `.values()` method:

```python
>>> print hello.values(name='Marcin')
[{'message': u'Hello Marcin'}]
```

To fetch results as a list of tuples use `.values_list()` method:

```python
>>> print hello.values_list(name='Marcin')
[(u'Hello Marcin',)]
```

To fetch results as iterator over tuples use `.iterator()` method:

```python
>>> print hello.iterator(name='Marcin')
<generator object _fetch at 0x7f8abd202870>
```

To fetch results as iterator over dictionaries use `.dictiterator()` method:

```python
>>> print hello.dictiterator(name='Marcin')
<generator object _fetch at 0x7f8abd202820>
```


## Advanced examples

### The Counter

Let's assume that we want to count rows returning from `hello.sql` query.
To do that we should create a sql for the counter. But instead of making
a new file, we'll create it from string, to show how `.from_string()`
works:

```python
>>> count = djsqltemplate.from_string(
    'select count(*) from ({{ sql|safe }}) x')
```

Then join the queries together:

```python
>>> import djsqltemplate
>>> hello = djsqltemplate.get('hello.sql').bind(name='Marcin')
>>> count = djsqltemplate.from_string(
    'select count(*) from ({{ sql|safe }}) x')
>>> print count.scalar(sql=hello)
1
```

As you can see the `:name` variable was replaced with `Marcin` string,
and the `sql` template variable (from The Counter query) was replaced
by `hello.sql` subquery.

#### How it looks?

```python
>>> print count.bind(sql=hello).pretty()
```
```sql
SELECT count(*)
FROM
  (SELECT 'Hello ' || :name AS message) x
```

#### How it works?

`count` and `hello` objects are `TemplateQuery` instances:

```python
>>> count, hello
(<sqltemplate.query.TemplateQuery at 0x7f8abd1ee610>,
 <sqltemplate.query.TemplateQuery at 0x7f8abd1ee210>)
```

The `TemplateQuery` wraps Django `Template` instance together with specified
context.  Calling `TemplateQuery` produces new instance with extended context
(internally using `.bind()` method), and the outermost context is extended by
context of embedded templates.

Context may be set at the factory time setting `context` argument or by
implicit call of `.bind()` method. Also you can pass extra context arguments
directly to `.values()`, `.values_list()`, `.iterator()`, `.dictiterator()` and
`.scalar()`.

```python
>>> hello = djsqltemplate.get('hello.sql', context={'name': 'Marcin'})
>>> print hello.context
{'name': 'Marcin'}

>>> hello = djsqltemplate.get('hello.sql')
>>> print hello.context
{}

>>> hello_marcin = hello.bind(name='Marcin')
>>> print hello_marcin.context
{'name': 'Marcin'}

>>> print hello.scalar(name='Marcin')
Hello Marcin
```

So in the Counter example we're setting `hello` instance as a `sql` variable
for the `counter.sql` template, which is resolved and rendered by
`{{ sql|safe }}` expression, and then (at the execution time) the `name`
variable is passed to `cursor.execute()` (which is safe and the preferred way
of passing query parameters). 

Remeber that preparing templates with additional context makes a new instance
(a copy) of the original object. This will allow you for easy query
customization dependend of your requirements.

### Countries searcher

Let's prepare a test table (still assuming sqlite as a db engine):

```bash
echo "create table countries (id int, name varchar(64));" | sqlite3 db.sqlite3
```

Fill the example data:

```sql
echo "insert into countries (id, name) values (1, 'Poland'), (2, 'Slovakia'), (3, 'Czech Republic');" | sqlite3 db.sqlite3
```

Add `countries.sql` query template:

```sql
select id, name from countries
{% if search_for %}where name like '%'||:search_for||'%'{% endif %}
{% if limit %}limit :limit{% endif %} 
```

Instantiate `count` and `countries` templates:

```python
>>> count = djsqltemplate.get('counter.sql')
>>> countries = djsqltemplate.get('countries.sql')
```

Ask for countries containg letter "a" in their names:

```python
>>> print countries.values(search_for='a')
[{'id': 1, 'name': u'Poland'}, {'id': 2, 'name': u'Slovakia'}]
```

then count the results:

```python
>>> print count.scalar(sql=countries.bind(search_for='a'))
2
```

and limit results if you want:

```python
>>> print countries.values(search_for='a', limit=1)
[{'id': 1, 'name': u'Poland'}]
```

Simple?

### Multiple database connections

`TemplateQuery` class provides `.using()` method which allow you to
change connection used to querying database. Just provide connection
name (alias) same as for Django's `QuerySet`.

```python
>>> print countries.using('default').values()
```

You can set connection name at factory time:

```python
>>> countries = djsqltemplate.get('countries.sql', using='default')
```

And you can use `djsqltemplate.using()` as a context manager:

```python
with djsqltemplate.using('default') as tpl:
    countries = tpl.get('countries.sql')
    print countries.values()
```

Please note that `tpl` variable is a new factory instance, which will
automatically set proper connection to all created `TemplateQuery`
objects. Direct call to `djsqltemplate.get()` will create objects same
as before, without connection set, because it is a shortcut for default
factory method.

### Default context

Sometimes you may need to set some defaults. To do that you can set
default context at a factory time:

```python
>>> countries = djsqltemplate.get('countries.sql', context={'limit': 2})
```

And by using `djsqltemplate.context()` context manager:

```python
with djsqltemplate.context(limit=1) as tpl:
    countries = tpl.get('countries.sql')
    print countries.values()
```

### Setting default context and connection together

If you want to set default context together with specific connection,
use `djsqltemplate.scope()` context manager:

```python
with djsqltemplate.scope(context={'limit': 2}, using='default') as tpl:
    countries = tpl.get('countries.sql')
    print countries.values()
```

## Motivation

* `django-sqltemplate` is designed for managing queries of mid/large complexity
  (like queries above 100 SLOCs, incl. window functions, non-generic syntax,
  etc)
* Maintenance of a complex queries is way faster using raw SQL instead of ORM
  objects (`Q()`,`F()`,`.aggregate()`, etc)
* The querying should be simplest as possible, incl. joining / embedding
  templates (we don't want to handle cursors and connections instances manually)
* It is not a replacement for Django ORM nor SQLAlchemy, and may be used
  together with (i.e.`sqlalchemy.text(str(countries(search_for='a')))`
  or Django's `Manager.raw()`)
* There are many good template engines (Django Templates, Jinja2), so we just
  need to use them and not reinvent the wheel
* Django 1.8+ has support for multiple templating engines
* Django is a most popoular RAD framework for Python, ~~but with limited ORM~~ (it's quite expressive nowdays, but still there are cases where plain SQL is better, ie. multiline and complex reporting queries)

## Requirements

* Django 1.11+, Django 2.x, Django 3.x
* Python 2.7 (deprecated), Python 3.5+

Dependencies:

* sqltemplate >= 0.5.0

## License

BSD

