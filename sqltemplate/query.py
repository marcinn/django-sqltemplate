from django.conf import settings
from django.db import connections, connection
from django.db.backends.utils import logger as db_logger
from django.utils.encoding import force_str, force_unicode

import flatdict
import types
from time import time

from .exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from .utils import prettify


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


class SQLResult(object):
    def __init__(self, cursor):
        self._cursor = cursor

    @property
    def cursor(self):
        return self._cursor


class SQLValuesResult(SQLResult):
    def __init__(self, *args, **kw):
        super(SQLValuesResult, self).__init__(*args, **kw)
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


class ValuesListResult(SQLValuesResult):
    def _fetch(self, cursor):
        return cursor.fetchall()

    def __len__(self):
        return len(self.result)


class ValuesResult(SQLValuesResult):
    def _fetch(self, cursor):
        return [
            dict(zip(self._columns, row))
            for row in cursor.fetchall()
            ]

    def __len__(self):
        return len(self.result)


class ValuesListIterator(SQLValuesResult):
    def _fetch(self, cursor):
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield row


class ValuesIterator(SQLValuesResult):
    def _fetch(self, cursor):
        while True:
            row = cursor.fetchone()
            if row is None:
                break
            yield dict(zip(self._columns, row))


class TemplateQuery(object):
    def __init__(self, template, context=None, using=None):
        self._template = template
        self._context = context or {}
        self._using = using
        self._sql = None

    @property
    def sql(self, using=None):
        if self._sql is None:
            self._sql = self.render()
        return self._sql

    def render(self):
        return self._template.render(self._context)

    @property
    def context(self):
        return self._context

    def bind(self, **context):
        ctx = dict(self._context)
        ctx.update(context)
        return self._clone(context=ctx)

    def using(self, using):
        return self._clone(using=using)

    def _cursor(self, using=None):
        using = using or self._using
        conn = connections[using] if using else connection
        return DictCursorWrapper(conn.cursor())

    def execute(self, using=None, result_class=SQLResult):
        def extract_subcontexts(values):
            subcontexts = []
            for value in values:
                try:
                    subctx = value.context
                except AttributeError:
                    pass
                else:
                    subcontexts.append(subctx)
                    subcontexts+= extract_subcontexts(subctx.values())
            return subcontexts

        ctx = {}

        for subcontext in extract_subcontexts(self._context.values()):
            ctx.update(subcontext)
        ctx.update(self._context)

        query_params = flatdict.FlatDict(ctx, delimiter='.').as_dict()

        cur = self._cursor(using=using or self._using)

        # Get native cursor to avoid problems with Django` DebugCursor
        # logging. See https://code.djangoproject.com/ticket/22377

        if settings.DEBUG:
            start = time()

        native_cursor = cur.cursor
        native_cursor.execute(force_str(self.sql), query_params)

        # Until Django bug #22377 is not resolved, we must manually
        # log query and append SQL to queries_log

        if settings.DEBUG:
            stop = time()
            duration = stop-start

            sql = cur.db.ops.last_executed_query(
                    native_cursor, self.sql, query_params)

            cur.db.queries_log.append({
                'sql': sql,
                'time': "%.3f" % duration,
            })

            db_logger.debug(
                '(%.3f) %s; args=%s', duration, self.sql, query_params,
                extra={'duration': duration, 'sql': self.sql, 'params': query_params}
            )

        return result_class(cur)

    def values(self, **extra):
        obj = self.bind(**extra) if extra else self
        return obj.execute(result_class=ValuesResult)

    def values_list(self, **extra):
        obj = self.bind(**extra) if extra else self
        return obj.execute(result_class=ValuesListResult)

    def iterator(self, **extra):
        obj = self.bind(**extra) if extra else self
        return obj.execute(result_class=ValuesListIterator)

    def dictiterator(self, **extra):
        obj = self.bind(**extra) if extra else self
        return obj.execute(result_class=ValuesIterator)

    def scalar(self, **extra):
        obj = self.bind(**extra) if extra else self
        result = obj.values_list(**extra)

        try:
            row = result[0]
        except IndexError:
            raise ObjectDoesNotExist('Query returned no rows')

        if len(result)>1:
            raise MultipleObjectsReturned('Query returned more than one row')

        return row[0]

    def rawtuple(self):
        return self.sql, self.context

    def pretty(self):
        return prettify(self.sql)

    def _clone(self, **kwargs):
        template = kwargs.pop('template', self._template)
        context = kwargs.pop('context', self._context)
        using = kwargs.pop('using', self._using)

        return type(self)(
            template=template, context=context, using=using, **kwargs)

    def __unicode__(self):
        return force_unicode(self.sql)

    def __str__(self):
        return force_str(unicode(self))
