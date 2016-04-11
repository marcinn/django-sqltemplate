
from django.template.utils import EngineHandler
from .settings import TEMPLATES


engines = EngineHandler(templates=TEMPLATES)


def get(template_name, **context):
    from .loader import get_template
    from .query import SQLTemplate

    return SQLTemplate(get_template(template_name), context=context)


def from_string(string, **context):
    from .query import SQLTemplate
    default_engine = engines.all()[0]
    return SQLTemplate(default_engine.from_string(string), context=context)


