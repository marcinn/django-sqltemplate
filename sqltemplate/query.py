from django.db import connections, connection
from django.utils.encoding import force_str
from .exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from .utils import prettify
import flatdict


class SQLTemplate(object):
    def __init__(self, template, context=None):
        self._template = template
        self._context = context or {}

    @property
    def context(self):
        return self._context

    def sql(self, using=None):
        return SQLQuery(self._template.render(self._context),
                context=self._context, using=using)

    def prepare(self, **extra):
        context = dict(self._context)
        context.update(extra)
        return type(self)(self._template, context=context)

    def __call__(self, **kw):
        return self.prepare(**kw)

    def values(self, using=None):
        return self.sql(using=using).values()

    def values_list(self, using=None):
        return self.sql(using=using).values_list()

    def iterator(self, using=None):
        return self.sql(using=using).iterator()

    def dictiterator(self, using=None):
        return self.sql(using=using).dictiterator()

    def scalar(self, using=None):
        return self.sql(using=using).scalar()

    def __str__(self):
        return str(self.sql())

    def __unicode__(self):
        return unicode(self.sql())

    def rawtuple(self):
        return self.sql().rawtuple()


class SQLResult(object):
    def __init__(self, cursor):
        self._cursor = cursor
        self._result = None
        self._columns = [col[0] for col in self._cursor.description]

    @property
    def result(self):
        if self._result is None:
            self._result = self._fetch(self._cursor)
        return self._result

    def __iter__(self):
        return iter(self.result)

    def _fetch(self, cursor):
        raise NotImplementedError

    def __str__(self):
        return str(self.result)

    def __getitem__(self, idx):
        return self.result[idx]


class ValuesListResult(SQLResult):
    def _fetch(self, cursor):
        return cursor.fetchall()

    def __len__(self):
        return len(self.result)


class ValuesResult(SQLResult):
    def _fetch(self, cursor):
        return [
            dict(zip(self._columns, row))
            for row in cursor.fetchall()
            ]

    def __len__(self):
        return len(self.result)


class ValuesListIterator(SQLResult):
    def _fetch(self, cursor):
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield row


class ValuesIterator(SQLResult):
    def _fetch(self, cursor):
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield dict(zip(self._columns, row))



class SQLQuery(object):
    def __init__(self, sql, context=None, using=None):
        self._sql = sql
        self._context = context or {}
        self._using = using

    @property
    def sql(self):
        return self._sql

    @property
    def context(self):
        return self._context

    def using(self, using):
        return self._clone(using=using)

    def _cursor(self, using=None):
        using = using or self._using
        conn = connections[using] if using else connection
        return DictCursorWrapper(conn.cursor())

    def execute(self, using=None, result_class=ValuesResult):
        def extract_subcontexts(values):
            subcontexts = []
            for value in values:
                if isinstance(value, (SQLTemplate, SQLQuery)):
                    subcontexts.append(value.context)
                    subcontexts+= extract_subcontexts(value.context.values())
            return subcontexts

        ctx = {}

        for subcontext in extract_subcontexts(self._context.values()):
            ctx.update(subcontext)
        ctx.update(self._context)

        query_params = flatdict.FlatDict(ctx, delimiter='.').as_dict()

        cur = self._cursor(using=using or self._using)
        cur.execute(self.sql, query_params)

        return result_class(cur)

    def values(self, using=None):
        return self.execute(using=using, result_class=ValuesResult)

    def values_list(self, using=None):
        return self.execute(using=using, result_class=ValuesListResult)

    def iterator(self, using=None):
        return self.execute(using=using, result_class=ValuesListIterator)

    def dictiterator(self, using=None):
        return self.execute(using=using, result_class=ValuesIterator)

    def scalar(self, using=None):
        result = self.values_list()

        try:
            row = result[0]
        except IndexError:
            raise ObjectDoesNotExist('Query returned no rows')

        if len(result)>1:
            raise MultipleObjectsReturned('Query returned more than one row')

        return row[0]

    def rawtuple(self):
        return self.sql, self.context

    def __unicode__(self):
        return prettify(self.sql)

    def __str__(self):
        return force_str(unicode(self))


class DictCursorWrapper(object):
    def __init__(self, cursor):
        self._cursor = cursor

    def __getattr__(self, attr):
        return getattr(self._cursor, attr)

    def dictfetchall(self):
        columns = [col[0] for col in self._cursor.description]
        return [
            dict(zip(columns, row))
            for row in self._cursor.fetchall()
            ]


