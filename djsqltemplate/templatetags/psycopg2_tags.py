from django.template import Library
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe

from psycopg2 import extensions

register = Library()


@register.filter
def adapt(x, qmark='%'):
    x = force_str(x)
    x = x.replace(qmark, qmark*2)  # escape psycopg2 paramstyle mark
    return mark_safe(extensions.adapt(x))
