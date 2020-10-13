from memcached_clients import RestclientPymemcacheClient
from uw_kws import ENCRYPTION_KEY_URL, ENCRYPTION_CURRENT_KEY_URL
import re

ONE_MINUTE = 60
ONE_HOUR = 60 * 60
ONE_DAY = 60 * 60 * 24
ONE_WEEK = 60 * 60 * 24 * 7
ONE_MONTH = 60 * 60 * 24 * 30


class Client(RestclientPymemcacheClient):
    def get_cache_expiration_time(self, service, url, status=None):
        if 'sws' == service:
            if re.match(r'^/student/v\d/term/', url):
                return ONE_DAY
            return ONE_HOUR

        if 'pws' == service:
            return ONE_DAY

        if 'kws' == service:
            if re.match(r'{}'.format(
                    ENCRYPTION_KEY_URL.format(r'[\-\da-fA-F]{36}')), url):
                return ONE_MONTH
            if re.match(r'{}'.format(
                    ENCRYPTION_CURRENT_KEY_URL.format(r"[\-\da-zA-Z]+")), url):
                return ONE_WEEK

        if 'nws' == service:
            if re.match(r'^/notification/v\d/person', url):
                return 5
            if re.match(r'^/notification/v\d/channel', url):
                return ONE_DAY

        if 'nws_auth' == service:
            return ONE_MINUTE * 20

    def delete_cached_kws_current_key(self, resource_type):
        self.deleteCache('kws', ENCRYPTION_CURRENT_KEY_URL.format(
            resource_type))
