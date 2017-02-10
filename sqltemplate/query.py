import flatdict

from .exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from .utils import prettify


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
    def __init__(self, adapter, template, context=None, using=None):
        self._adapter = adapter
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
        return self._adapter.render_template(self._template, self._context)

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
        return self._adapter.create_cursor(using=using)

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
                    subcontexts += extract_subcontexts(subctx.values())
            return subcontexts

        ctx = {}

        for subcontext in extract_subcontexts(self._context.values()):
            ctx.update(subcontext)
        ctx.update(self._context)

        query_params = flatdict.FlatDict(ctx, delimiter='.').as_dict()
        cur = self._adapter.do_query(
                sql=self.sql, query_params=query_params,
                using=using or self._using)

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

        if len(result) > 1:
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
            adapter=self._adapter, template=template,
            context=context, using=using, **kwargs)

    def __unicode__(self):
        return self.sql
