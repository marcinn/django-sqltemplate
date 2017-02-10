# Backward compatibility (django-only)

try:
    from .contrib.django import (  # NOQA
            service, context, using, scope, DjangoAdapter,
            from_string, get)
except ImportError:
    from .base import SQLTemplate
else:
    from .base import SQLTemplate as BaseSQLTemplate

    class SQLTemplate(BaseSQLTemplate):
        def __init__(self, using=None, context=None):  # NOQA
            super(BaseSQLTemplate, self).__init__(
                    adapter=DjangoAdapter, using=using, context=context)
