from .base_settings import *
import os

ALLOWED_HOSTS = ['*']

INSTALLED_APPS += [
    'notify.apps.NotifyUIConfig',
    'supporttools',
    'userservice',
    'persistent_message',
    'rc_django',
    'django_user_agents',
    'compressor',
]

MIDDLEWARE += [
    'userservice.user.UserServiceMiddleware',
    'django_user_agents.middleware.UserAgentMiddleware',
]

TEMPLATES[0]['OPTIONS']['context_processors'].extend([
    'supporttools.context_processors.supportools_globals',
])

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

COMPRESS_OFFLINE = True
COMPRESS_OFFLINE_CONTEXT = {
    'wrapper_template': 'persistent_message/manage_wrapper.html',
}

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

RESTCLIENTS_NWS_DAO_CLASS = 'Live'
RESTCLIENTS_NWS_TIMEOUT = os.getenv('NWS_TIMEOUT', 2)
RESTCLIENTS_NWS_POOL_SIZE = os.getenv('NWS_POOL_SIZE', 10)
RESTCLIENTS_NWS_AUTH_DAO_CLASS = RESTCLIENTS_NWS_DAO_CLASS
RESTCLIENTS_NWS_AUTH_TIMEOUT = RESTCLIENTS_NWS_TIMEOUT
RESTCLIENTS_NWS_AUTH_POOL_SIZE = RESTCLIENTS_NWS_POOL_SIZE
if os.getenv('NWS_ENV') == 'PROD':
    RESTCLIENTS_NWS_CERT_FILE = APPLICATION_CERT_PATH
    RESTCLIENTS_NWS_KEY_FILE = APPLICATION_KEY_PATH
    RESTCLIENTS_NWS_HOST = 'https://api.concert.uw.edu'
else:
    RESTCLIENTS_NWS_AUTH_SECRET = os.getenv('NWS_AUTH_SECRET')
    RESTCLIENTS_NWS_AUTH_HOST = 'https://auth.api.notify-dev.sis.uw.edu'
    RESTCLIENTS_NWS_HOST = 'https://api.notify-dev.sis.uw.edu'

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
