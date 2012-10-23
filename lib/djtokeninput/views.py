#!/usr/bin/env python

import json
from django import http
from django.views.generic import View
from django.views.generic.list import MultipleObjectMixin
from django.core.exceptions import ImproperlyConfigured

try:
    from django.settings import DJTOKENINPUT_LOOKUPS as lookups
except ImportError:
    raise ImproperlyConfigured("DJTOKENINPUT_LOOKUPS is not defined in your settings")


class JSONLookupView(MultipleObjectMixin, View):

    query_parameter = "q"
    min_query_length = 1
    response_class = http.HttpResponse
    allow_empty = True

    def filter_queryset(self, qs, query):
        """This method should take a queryset in qs, and return a queryset, filtered in some way by
        query."""
        raise NotImplemented, "This method must be overridden"

    def get(self, request, *args, **kwargs):
        self.query = request.GET.get(self.query_parameter, "")
        self.object_list = self.filter_queryset(self.get_queryset(), self.query)
        allow_empty = self.get_allow_empty()
        if not allow_empty and len(self.object_list) == 0:
            raise Http404(_(u"Empty list and '%(class_name)s.allow_empty' is False.")
                          % {'class_name': self.__class__.__name__})
        context = self.get_context_data(object_list=self.object_list)
        return self.render_to_response(context)

    def json_filter(self, context):
        return ( dict(id=o.id, name=unicode(o)) for o in context.object_list )

    def render_to_response(self, context):
        return self.response_class(
            json.dumps(self.json_filter(context)),
            content_type = "application/json",
        )

