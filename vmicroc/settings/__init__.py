import os

if os.environ.get('DJANGO_DEVELOPMENT'):
    from vmicroc.settings.development import *
else:
    from vmicroc.settings.deployment import *

from vmicroc.settings.secrets import *
