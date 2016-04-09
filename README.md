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

### Install the package

```pip install django-sqltemplate```

### Add SQL template(s)

Make `sqltemplates` directory in your Django app (your app must be added to `INSTALLED_APPS`):

```mkdir <django-project>/<my-app>/sqltemplates```

Put `hello.sql` template in `sqltemplates` directory:

hello.sql (assuming sqlite syntax)
```sql
select 'Hello ' || :name as message
```

### Query the database

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


## Advanced examples

### The Counter

Let's assume that we want to count rows returning from `hello.sql` query.
To do that we should create a sql for the counter  (name it `counter.sql`
and place in the same directory as `hello.sql`):

```sql
select count(*) from ({{ sql|safe }}) x
```

Then join the queries together:

```python
>>> import sqltemplate
>>> hello = sqltemplate.get('hello.sql')
>>> count = sqltemplate.get('counter.sql')
>>> print count(sql=hello(name='Marcin')).scalar()
1
```

As you can see the `:name` variable was replaced with `Marcin` string,
and the `sql` template variable (from The Counter query) was replaced
by `hello.sql` subquery.

#### How it looks?

```python
>>> print count(sql=hello(name='Marcin'))
```
```sql
SELECT count(*)
FROM
  (SELECT 'Hello ' || :name AS message) x
```

#### How it works?

`count` and `hello` objects are `SQLTeamplate` instances:

```python
>>> count, hello
(<sqltemplate.query.SQLTemplate at 0x7f8abd1ee610>,
 <sqltemplate.query.SQLTemplate at 0x7f8abd1ee210>)
```

The `SQLTemplate` wraps Django `Template` instance together with specified context.
Calling `SQLTemplate` produces new instance with extended context (internally using `.prepare()` method),
and the outermost context is extended by context of embedded templates.

Context may be set at the factory time:

```python
>>> hello = sqltemplate.get('hello.sql', name='Marcin')
>>> print hello.context
{'name': 'Marcin'}
```

or on demand by using `.prepare()` or simple calling the instance:

```python
>>> hello = sqltemplate.get('hello.sql')
>>> print hello.context
{}

>>> hello_marcin = hello.prepare(name='Marcin')
>>> print hello_marcin.context
{'name': 'Marcin'}

>>> hello_marcin = hello(name='Marcin')
>>> print hello_marcin.context
{'name': 'Marcin'}
```

So in the Counter example we're setting `hello` instance as a `sql` variable for 
the `counter.sql` template, which is resolved and rendered by `{{ sql|safe }}` expression,
and then (at the execution time) the `name` variable is passed to `cursor.execute()`
(which is safe and the preferred way of passing query parameters). 

Remeber that preparing templates with additional context, makes a new instance (a copy)
of the original object. This will allow you for easy query customization dependend of
your requirements.

### Countries counter

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
>>> count = sqltemplate.get('counter.sql')
>>> countries = sqltemplate.get('countries.sql')
```

And query for countries containg letter "a" in their names:

```python
>>> print countries(search_for='a').values()
[{'id': 1, 'name': u'Poland'}, {'id': 2, 'name': u'Slovakia'}]
```

then count the results:

```python
>>> print count(sql=countries(search_for='a')).scalar()
2
```

and limit results if you want:

```python
>>> print countries(search_for='a', limit=1).values()
[{'id': 1, 'name': u'Poland'}]
```

Simple?

## Requirements

* Django 1.8+

Dependencies:

* sqlparse
* flatdict

## License

BSD

