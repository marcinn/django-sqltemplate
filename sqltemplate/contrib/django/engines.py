from __future__ import absolute_import

from django.template.utils import EngineHandler
from .settings import TEMPLATES

engines = EngineHandler(templates=TEMPLATES)
