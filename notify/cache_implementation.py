from rc_django.cache_implementation import TimedCache
from rc_django.cache_implementation.memcache import MemcachedCache
from uw_kws import ENCRYPTION_KEY_URL, ENCRYPTION_CURRENT_KEY_URL
import re

ONE_MINUTE = 60
ONE_HOUR = 60 * 60
ONE_DAY = 60 * 60 * 24
ONE_WEEK = 60 * 60 * 24 * 7
ONE_MONTH = 60 * 60 * 24 * 30


def get_cache_time(service, url):
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
        if re.match(r'^/notification/v\d/channel', url):
            return ONE_DAY

    if 'nwsauth' == service:
        return ONE_MINUTE * 20


class NotifyMemcachedCache(MemcachedCache):
    def get_cache_expiration_time(self, service, url):
        return get_cache_time(service, url)

    def delete_cached_kws_current_key(self, resource_type):
        self.deleteCache('kws', ENCRYPTION_CURRENT_KEY_URL.format(
            resource_type))

    def delete_cached_kws_key(self, key_id):
        self.deleteCache('kws', ENCRYPTION_KEY_URL.format(key_id))


class UICache(TimedCache):
    def delete_cached_kws_current_key(self, resource_type):
        self.deleteCache('kws', ENCRYPTION_CURRENT_KEY_URL.format(
            resource_type))

    def delete_cached_kws_key(self, key_id):
        self.deleteCache('kws', ENCRYPTION_KEY_URL.format(key_id))

    def getCache(self, service, url, headers):
        return self._response_from_cache(
            service, url, headers, get_cache_time(service, url))

    def processResponse(self, service, url, response):
        return self._process_response(service, url, response)
