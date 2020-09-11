from .base_settings import *
import os

INSTALLED_APPS += [
    'notify.apps.NotifyUIConfig',
    'supporttools',
    'userservice',
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

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'add_user': {
            '()': 'notify.log.UserFilter'
        },
        'stdout_stream': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda record: record.levelno <= logging.WARNING
        },
        'stderr_stream': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda record: record.levelno >= logging.ERROR
        }
    },
    'formatters': {
        'ui': {
            'format': '%(levelname)-4s %(asctime)s %(user)s %(actas)s %(message)s [%(name)s]',
            'datefmt': '[%Y-%m-%d %H:%M:%S]',
        },
        'restclients_timing': {
            'format': '%(levelname)-4s restclients_timing %(module)s %(asctime)s %(message)s [%(name)s]',
            'datefmt': '[%Y-%m-%d %H:%M:%S]',
        },
        'events': {
            'format': '%(levelname)-4s event %(asctime)s %(message)s [%(name)s]',
            'datefmt': '[%Y-%m-%d %H:%M:%S]',
        },
    },
    'handlers': {
        'stdout': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'filters': ['add_user', 'stdout_stream'],
            'formatter': 'ui',
        },
        'stderr': {
            'class': 'logging.StreamHandler',
            'stream': sys.stderr,
            'filters': ['add_user', 'stderr_stream'],
            'formatter': 'ui',
        },
        'event_log': {
            'filters': ['stdout_stream'],
            'formatter': 'events',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        },
        'ui_log': {
            'filters': ['add_user', 'stdout_stream'],
            'formatter': 'ui',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        },
        'restclients_timing': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'filters': ['stdout_stream'],
            'formatter': 'restclients_timing',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django.security.DisallowedHost': {
            'handlers': ['null'],
            'propagate': False,
        },
        'django.request': {
            'handlers': ['stderr'],
            'level': 'ERROR',
            'propagate': True,
        },
        'notify': {
            'handlers': ['ui_log'],
            'level': 'INFO',
            'propagate': True,
        },
        'notify.events': {
            'handlers': ['event_log'],
            'level': 'INFO',
            'propagate': False,
        },
        'restclients_core': {
            'handlers': ['restclients_timing'],
            'level': 'INFO',
            'propagate': False,
        },
        '': {
            'handlers': ['stdout', 'stderr'],
            'level': 'INFO' if os.getenv('ENV', 'localdev') == 'prod' else 'DEBUG'
        }
    }
}

if os.getenv('ENV') == 'localdev':
    DEBUG = True
    NOTIFY_ADMIN_GROUP = 'u_test_group'
    RESTCLIENTS_DAO_CACHE_CLASS = None
else:
    NOTIFY_ADMIN_GROUP = os.getenv('ADMIN_GROUP', '')
    RESTCLIENTS_DAO_CACHE_CLASS = 'notify.cache_implementation.NotifyMemcachedCache'

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
SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL_ADDRESS', '')
SENDER_ADDRESS = os.getenv('EMAIL_SENDER_ADDRESS', '')

INVALID_UUIDS = [
    '00000000-0000-0000-0000-000000000000'
]
