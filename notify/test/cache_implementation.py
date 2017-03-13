from restclients.dao import SWS_DAO, NWS_DAO
from restclients.models import CacheEntryTimed
from restclients.test import fdao_sws_override
from notify.cache_implementation import UICache
from django.test import TestCase
from datetime import timedelta


@fdao_sws_override
class UICacheTest(TestCase):
    def test_cached_404(self):
        with self.settings(
                RESTCLIENTS_DAO_CACHE_CLASS='notify.cache_implementation.UICache'):
            error_url = '/student/v4/term/notfound'
            cache = UICache()
            response = cache.getCache('sws', error_url, {})
            self.assertEquals(response, None)

            sws = SWS_DAO()
            sws.getURL(error_url, {})
            response = cache.getCache('sws', error_url, {})
            self.assertEquals(response["response"].status, 404)

            query = CacheEntryTimed.objects.filter(
                                                service="sws",
                                                url=error_url,
                                              )


            # Make sure we don't cache errors for more than 5 minutes
            cache_entry = query[0]
            cache_entry.time_saved = cache_entry.time_saved - timedelta(minutes=5)
            cache_entry.save()

            response = cache.getCache('sws', error_url, {})
            self.assertEquals(response, None)


    def test_sws_resources(self):
        with self.settings(
                RESTCLIENTS_DAO_CACHE_CLASS='notify.cache_implementation.UICache'):

            should_be_cached_url = '/student/v4/term/current.json'
            no_cache_url = '/student/v4/course/2012,autumn,CSE,100/W.json'

            cache = UICache()
            response = cache.getCache('sws', should_be_cached_url, {})
            self.assertEquals(response, None)

            sws = SWS_DAO()
            sws.getURL(should_be_cached_url, {})

            query = CacheEntryTimed.objects.filter(
                                                service="sws",
                                                url=should_be_cached_url,
                                              )


            # Make sure that the cached entry is still used 8 hours later.
            cache_entry = query[0]
            cache_entry.time_saved = cache_entry.time_saved - timedelta(hours=8)
            cache_entry.save()

            response = cache.getCache('sws', should_be_cached_url, {})
            self.assertEquals(response["response"].status, 200)

            response = cache.getCache('sws', no_cache_url, {})
            self.assertEquals(response, None)

            sws = SWS_DAO()
            sws.getURL(no_cache_url, {})

            query = CacheEntryTimed.objects.filter(
                                                service="sws",
                                                url=no_cache_url,
                                              )


            # Make sure that the cached entry is not used 1 minute later
            cache_entry = query[0]
            cache_entry.time_saved = cache_entry.time_saved - timedelta(minutes=1)
            cache_entry.save()

            response = cache.getCache('sws', no_cache_url, {})
            self.assertEquals(response, None)


    def test_nws_resources(self):
        with self.settings(
                RESTCLIENTS_DAO_CACHE_CLASS='notify.cache_implementation.UICache'):


            should_be_cached_url = '/notification/v1/channel?tag_year=2013&tag_quarter=autumn&max_results=1'
            no_cache_url = '/notification/v1/template/9a2cfb4c-8120-45c6-a7a6-9eac7cf95050'
            cache = UICache()

            response = cache.getCache('nws', should_be_cached_url, {})
            self.assertEquals(response, None)

            nws = NWS_DAO()
            nws.getURL(should_be_cached_url, {})

            query = CacheEntryTimed.objects.filter(
                                                service="nws",
                                                url=should_be_cached_url,
                                              )


            # Make sure that the cached entry is still used 8 hours later.
            cache_entry = query[0]
            cache_entry.time_saved = cache_entry.time_saved - timedelta(hours=8)
            cache_entry.save()

            response = cache.getCache('nws', should_be_cached_url, {})
            self.assertEquals(response["response"].status, 200)

            nws.getURL(no_cache_url, {})

            query = CacheEntryTimed.objects.filter(
                                                service="nws",
                                                url=no_cache_url,
                                              )


            # Make sure that the cached entry is not used 1 minute later
            cache_entry = query[0]
            cache_entry.time_saved = cache_entry.time_saved - timedelta(minutes=1)
            cache_entry.save()

            response = cache.getCache('nws', no_cache_url, {})
            self.assertEquals(response, None)
