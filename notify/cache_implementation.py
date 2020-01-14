from rc_django.cache_implementation import TimedCache
from rc_django.models import CacheEntryTimed
from uw_kws import ENCRYPTION_KEY_URL, ENCRYPTION_CURRENT_KEY_URL
import re


class UICache(TimedCache):
    """ A custom cache implementation for CAN """

    url_policies = {}
    url_policies["sws"] = (
        (re.compile(r"^/student/v\d/term/"), 60 * 60 * 10),
    )
    url_policies["pws"] = (
        (re.compile(r"^/identity/v\d/person/"), 60 * 60 * 24 * 7),
    )
    url_policies["nws"] = (
        (re.compile(r"^/notification/v\d/channel"), 60 * 60 * 10),
    )
    url_policies["kws"] = (
        (re.compile(r"{}".format(
            ENCRYPTION_KEY_URL.format(r'[\-\da-fA-F]{36}'))),
            60 * 60 * 24 * 30),
        (re.compile(r"{}".format(
            ENCRYPTION_CURRENT_KEY_URL.format(r"[\-\da-zA-Z]+"))),
            60 * 60 * 24 * 7),
    )

    def deleteCache(self, service, url):
        try:
            entry = CacheEntryTimed.objects.get(service=service, url=url)
            entry.delete()
        except CacheEntryTimed.DoesNotExist:
            return

    def delete_cached_kws_current_key(self, resource_type):
        self.deleteCache('kws', ENCRYPTION_CURRENT_KEY_URL.format(
            resource_type))

    def delete_cached_kws_key(self, key_id):
        self.deleteCache('kws', ENCRYPTION_KEY_URL.format(key_id))

    def _get_cache_policy(self, service, url):
        for policy in UICache.url_policies.get(service, []):
            if policy[0].search(url):
                return policy[1]
        return 0

    def getCache(self, service, url, headers):
        cache_policy = self._get_cache_policy(service, url)
        return self._response_from_cache(service, url, headers, cache_policy)

    def processResponse(self, service, url, response):
        if self._get_cache_policy(service, url):
            return self._process_response(service, url, response)
