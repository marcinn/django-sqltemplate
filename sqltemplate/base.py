
class SQLTemplate(object):
    def __init__(self, adapter, using=None, context=None):
        self._using = using
        self._context = context or {}
        self._adapter = adapter

    def get(self, template_name, context=None, using=None):
        from .query import TemplateQuery

        ctx = dict(self._context)
        ctx.update(context or {})

        return TemplateQuery(
                adapter=self._adapter,
                template=self._adapter.load_template(template_name),
                context=ctx, using=using or self._using)

    def from_string(self, string, context=None, using=None):
        from .query import TemplateQuery

        ctx = dict(self._context)
        ctx.update(context or {})

        return TemplateQuery(
                adapter=self._adapter,
                template=self._adapter.create_template_from_string(string),
                context=ctx, using=using or self._using)
