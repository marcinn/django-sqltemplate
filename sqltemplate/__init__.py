
from django.template.utils import EngineHandler
from .settings import TEMPLATES
import contextlib


engines = EngineHandler(templates=TEMPLATES)


class SQLTemplate(object):
    def __init__(self, using=None, context=None):
        self._using = using
        self._context = context or {}

    def get(self, template_name, context=None, using=None):
        from .loader import get_template
        from .query import TemplateQuery

        ctx = dict(self._context)
        ctx.update(context or {})

        return TemplateQuery(
                template=get_template(template_name),
                context=ctx, using=using or self._using
                )

    def from_string(self, string, context=None, using=None):
        from .query import TemplateQuery

        default_engine = engines.all()[0]

        ctx = dict(self._context)
        ctx.update(context or {})

        return TemplateQuery(
                template=default_engine.from_string(string),
                context=ctx, using=using or self._using
                )


service = SQLTemplate()


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

