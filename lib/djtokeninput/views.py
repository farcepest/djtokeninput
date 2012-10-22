#!/usr/bin/env python

import json
from django import http
from django.core.exceptions import ImproperlyConfigured

try:
    from django.settings import DJTOKENINPUT_LOOKUPS as lookups
except ImportError:
    raise ImproperlyConfigured("DJTOKENINPUT_LOOKUPS is not defined in your settings")


def lookup(request, channel):
    query = request.GET.get("q", "")
    if not query:
        return http.HttpResponse(
            json.dumps([]),
            content_type = "application/json",
        )

    try:
        lookup = lookups[channel]
    except KeyError:
        raise http.Http404

    if not callable(lookup):
        try:
            mod, cls = lookup.rsplit('.', 1)
            lookup_module = __import__(mod, {}, {}, [''])
        except ImportError:
            raise ImproperlyConfigured("DJTOKENINPUT_LOOKUP channel '%s' lookup module '%s' couldn't be imported" % (channel, mod))

        try:
            lookup_cls = getattr(lookup_module, cls)
        except AttributeError:
            raise ImproperlyConfigured("DJTOKENINPUT_LOOKUP channel '%s' couldn't import lookup class '%s' from '%s'" % (channel, cls, mod))

        if not callable(lookup_cls):
            raise ImproperlyConfigured("DJTOKENINPUT_LOOKUP channel '%s' does not point to a callable object or class" % channel)

        lookup = lookups[channel] = lookup_cls # may be evil, probably should use a real cache

    results = lookup(request, query)

    return http.HttpResponse(
        results.as_json(),
        content_type = "application/json",
    )

