from restclients.cache_implementation import TimedCache
import re


class UICache(TimedCache):
    """ A custom cache implementation for CAN """

    url_policies = {}
    url_policies["sws"] = (
        (re.compile(r"^/student/v4/term/"), 60 * 60 * 10),
    )
    url_policies["pws"] = (
        (re.compile(r"^/identity/v1/person/"), 60 * 60 * 24 * 7),
    )
    url_policies["nws"] = (
        (re.compile(r"^/notification/v1/channel"), 60 * 60 * 10),
    )

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
