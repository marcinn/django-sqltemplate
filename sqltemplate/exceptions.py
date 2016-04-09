try:
    from django.template.exceptions import TemplateDoesNotExist
except ImportError:
    from django.template.base import TemplateDoesNotExist

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
