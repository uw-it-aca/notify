from .base_settings import *
import os

ALLOWED_HOSTS = ['*']

CACHES = {
    'default' : {
        'BACKEND' : 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION' : 'notify_sessions'
    }
}

INSTALLED_APPS += [
    'compressor',
    'django_user_agents',
    'userservice',
    'supporttools',
    'persistent_message',
    'rc_django',
    'notify.apps.NotifyUIConfig',
]

MIDDLEWARE += [
    'userservice.user.UserServiceMiddleware',
    'django_user_agents.middleware.UserAgentMiddleware',
]

TEMPLATES[0]['OPTIONS']['context_processors'].extend([
    'supporttools.context_processors.supportools_globals',
])

COMPRESS_OFFLINE = True
COMPRESS_ROOT = '/static/'

STATICFILES_FINDERS += (
    'compressor.finders.CompressorFinder',
)

COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
    ('text/x-sass', 'pyscss {infile} > {outfile}'),
    ('text/x-scss', 'pyscss {infile} > {outfile}'),
)

COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter'
]

COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter',
]

if os.getenv('ENV') == 'localdev':
    DEBUG = True
    NOTIFY_ADMIN_GROUP = 'u_test_group'
    RESTCLIENTS_DAO_CACHE_CLASS = None
else:
    NOTIFY_ADMIN_GROUP = os.getenv('ADMIN_GROUP', '')
    RESTCLIENTS_DAO_CACHE_CLASS = 'notify.cache_implementation.NotifyMemcachedCache'
    if os.getenv('ENV') == 'prod':
        APP_SERVER_BASE = 'https://notify.uw.edu'

USERSERVICE_VALIDATION_MODULE = 'notify.utilities.validate_override_user'
USERSERVICE_OVERRIDE_AUTH_MODULE = 'notify.views.can_override_user'
RESTCLIENTS_ADMIN_AUTH_MODULE = 'notify.views.can_proxy_restclient'
PERSISTENT_MESSAGE_AUTH_MODULE = 'notify.views.can_manage_persistent_messages'

AWS_CA_BUNDLE = RESTCLIENTS_CA_BUNDLE
AWS_SQS = {
    'ENROLLMENT_V2': {
        'QUEUE_ARN': os.getenv('SQS_ENROLLMENT_QUEUE_ARN', ''),
        'KEY_ID': os.getenv('SQS_ENROLLMENT_KEY_ID', ''),
        'KEY': os.getenv('SQS_ENROLLMENT_KEY', ''),
        'VISIBILITY_TIMEOUT': 60,
        'MESSAGE_GATHER_SIZE': 10,
        'VALIDATE_SNS_SIGNATURE': True,
        'VALIDATE_BODY_SIGNATURE': True,
        'EVENT_COUNT_PRUNE_AFTER_DAY': 2,
    },
}

GOOGLE_ANALYTICS_KEY = os.getenv('GOOGLE_ANALYTICS_KEY', '')
SUPPORTTOOLS_PARENT_APP = 'Notify.UW'
SUPPORTTOOLS_PARENT_APP_URL = '/'
SUPPORT_EMAIL = 'help@uw.edu'
SENDER_ADDRESS = 'notify@uw.edu'

INVALID_UUIDS = [
    '00000000-0000-0000-0000-000000000000'
]
