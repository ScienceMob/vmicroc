import os

if os.environ.get('DJANGO_DEVELOPMENT'):
    from vmicroc.settings.development import *
else:
    from vmicroc.settings.production import *
