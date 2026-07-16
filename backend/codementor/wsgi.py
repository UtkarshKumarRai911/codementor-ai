"""WSGI config for CodeMentor AI project."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codementor.settings")

application = get_wsgi_application()
