from django.http import HttpResponse
from django.views.decorators.cache import never_cache
import json
import re


class RESTDispatch(object):
    """ Handles passing on the request to the correct view method
        based on the request type.
    """
    @never_cache
    def run(self, *args, **named_args):
        return self.run_http_method(*args, **named_args)

    def run_http_method(self, *args, **named_args):
        request = args[0]

        if (re.match(r"(GET|HEAD|POST|PUT|DELETE|PATCH)", request.method) and
                hasattr(self, request.method)):
            return getattr(self, request.method)(*args, **named_args)
        else:
            return self.invalid_method(*args, **named_args)

    def invalid_method(self, *args, **named_args):
        return HttpResponse("Method not allowed", status=405)

    def error_response(self, status=400, message="", content={}):
        content["error"] = message
        content["status"] = status
        return HttpResponse(json.dumps(content),
                            status=status,
                            content_type="application/json")

    def json_response(self, content="", status=200):
        return HttpResponse(json.dumps(content),
                            status=status,
                            content_type="application/json")
