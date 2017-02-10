from __future__ import absolute_import

from django.conf import settings


TEMPLATES = getattr(settings, 'SQL_TEMPLATES', [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': False,
    'OPTIONS': {
        'loaders': [
            'django.template.loaders.filesystem.Loader',
            'djsqltemplate.loaders.app_directories.Loader',
            ]
        },
    }])

