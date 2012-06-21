import os
import sys

sys.path.append('/srv/rainmap/django')
sys.path.append('/srv/rainmap/django/rainmap')
sys.path.append('/srv/rainmap/celeryd')

os.environ['DJANGO_SETTINGS_MODULE'] = 'rainmap.settings'
os.environ["CELERY_LOADER"] = 'django'
# os.environ['PYTHON_EGG_CACHE'] = '/tmp'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
