
from django.template.utils import EngineHandler
from .settings import TEMPLATES


engines = EngineHandler(templates=TEMPLATES)


def get(template_name, **context):
    from .loader import get_template
    from .query import SQLTemplate

    return SQLTemplate(get_template(template_name), context=context)
