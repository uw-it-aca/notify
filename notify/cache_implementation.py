from rc_django.cache_implementation import TimedCache
import re


class UICache(TimedCache):
    """ A custom cache implementation for CAN """

    kws_url_current_key = '/key/v1/type/%s/encryption/current'
    kws_url_key = '/key/v1/encryption/%s.json'

    url_policies = {}
    url_policies["sws"] = (
        (re.compile(r"^/student/v5/term/"), 60 * 60 * 10),
    )
    url_policies["pws"] = (
        (re.compile(r"^/identity/v1/person/"), 60 * 60 * 24 * 7),
    )
    url_policies["nws"] = (
        (re.compile(r"^/notification/v1/channel"), 60 * 60 * 10),
    )
    url_policies["kws"] = (
        (re.compile(r"^%s" % (
            kws_url_key % '[\-\da-fA-F]{36}\\')), 60 * 60 * 24 * 30),
        (re.compile(r"^%s" % (
            kws_url_current_key % "[\-\da-zA-Z]+")), 60 * 60 * 24 * 7),
    )

    def deleteCache(self, service, url):
        try:
            entry = CacheEntryTimed.objects.get(service=service, url=url)
            entry.delete()
        except CacheEntryTimed.DoesNotExist:
            return

    def delete_cached_kws_current_key(self, resource_type):
        self.deleteCache('kws', self.kws_url_current_key % resource_type)

    def delete_cached_kws_key(self, key_id):
        self.deleteCache('kws', self.kws_url_key % key_id)

    def getCache(self, service, url, headers):
        cache_time = 0
        if service in UICache.url_policies:
            service_policies = UICache.url_policies[service]

            for policy in service_policies:
                pattern = policy[0]
                policy_cache_time = policy[1]

                if pattern.match(url):
                    cache_time = policy_cache_time

        return self._response_from_cache(service, url, headers, cache_time)

    def processResponse(self, service, url, response):
        return self._process_response(service, url, response)
