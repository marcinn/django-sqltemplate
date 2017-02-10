from __future__ import absolute_import

import contextlib
from time import time

from django.db import connections, connection
from django.db.backends.utils import logger as db_logger
from django.utils.encoding import force_str

from .loader import get_template
from .engines import engines

from ...base import SQLTemplate


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


class DjangoAdapter(object):
    def __init__(self):
        from django.conf import settings
        self.debug = settings.DEBUG

    def load_template(self, template_name):
        return get_template(template_name)

    def create_cursor(self, using=None):
        conn = connections[using] if using else connection
        return DictCursorWrapper(conn.cursor())

    def create_template_from_string(self, string):
        default_engine = engines.all()[0]
        return default_engine.from_string(string)

    def render_template(self, template, context=None):
        return template.render(context)

    def do_query(self, sql, query_params, using=None):
        cur = self.create_cursor(using=using)

        # Get native cursor to avoid problems with Django` DebugCursor
        # logging. See https://code.djangoproject.com/ticket/22377

        if self.debug:
            start = time()

        native_cursor = cur.cursor
        native_cursor.execute(force_str(sql), query_params)

        # Until Django bug #22377 is not resolved, we must manually
        # log query and append SQL to queries_log

        if self.debug:
            stop = time()
            duration = stop-start

            sql = cur.db.ops.last_executed_query(
                    native_cursor, sql, query_params)

            cur.db.queries_log.append({
                'sql': sql,
                'time': "%.3f" % duration,
            })

            db_logger.debug(
                '(%.3f) %s; args=%s', duration, sql, query_params,
                extra={
                    'duration': duration, 'sql': sql,
                    'params': query_params}
            )

        return cur


service = SQLTemplate(adapter=DjangoAdapter())


def get(*args, **kw):
    return service.get(*args, **kw)


def from_string(*args, **kw):
    return service.from_string(*args, **kw)


@contextlib.contextmanager
def context(**context):
    yield SQLTemplate(context=context)


@contextlib.contextmanager
def using(name):
    yield SQLTemplate(using=name)


@contextlib.contextmanager
def scope(context=None, using=None):
    yield SQLTemplate(using=using, context=context)
