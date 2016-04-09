# django-sqltemplate
Database query tool for Django, based on SQL templates

## Introduction

SQL is a great and poweruful DSL, which is easeier in maintenance 
when you're working on complext queries (i.e. reporting queries).

But the main problem with raw SQL is a "spaghetti" anti-pattern, 
when you're embedding/building SQLs in directly in your code.

The solution comes from templating SQLs idea and `django-sqltemplate` 
is a simple implementation of it.

## Quickstart

Install package:

```pip install django-sqltemplate```

Make `sqltemplates` directory in your Django app:

```mkdir <django-project>/<my-app>/sqltemplates```

Put `hello.sql` template in `sqltemplates``` directory:

hello.sql (assuming sqlite syntax)
```
select 'Hello ' || :name as message;
```

Execute the query:

```
[1]: import sqltemplate
[2]: hello = sqltemplate.get('hello.sql')
[3]: print hello(name='Marcin').values()
[{'message': u'Hello Marcin'}]
```

If query returns just one row (as in example above) you may read result directly using `.scalar()` method:

```
[4]: print hello(name='Marcin').scalar()
Hello Marcin
```

