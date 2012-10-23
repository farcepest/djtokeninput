#!/usr/bin/env python

import json
from django.http import Http404, HttpResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from django.views.generic.list import MultipleObjectMixin

class JSONSearchView(MultipleObjectMixin, View):

    query_parameter = "q"
    min_query_length = 1
    queryset_limit_factor = 10
    queryset_limit_max = 50
    response_class = HttpResponse
    allow_empty = True

    def get_max_results(self):
        """
        Computes the upper bound for the size of the result set.
        :return:
            Returns the maximum number of results allowed for this particular query.
            This is computed as:
                (length of query string)*(minimum query length)*(queryset limit factor)
            i.e. longer query strings allow for a longer result set.
            queryset_limit_max is the absolute upper limit, if set to a non-False value.
            Note that an empty query string (length 0) generates a limit of 0.
        :rtype:
            int
        """
        query_length = len(self.query.strip())
        max_results = self.min_query_length*query_length*self.queryset_limit_factor
        if self.queryset_limit_max:
            return max(max_results, self.queryset_limit_max)
        else:
            return max_results

    def limit_queryset(self, qs):
        M = self.get_max_results()
        if M:
            return qs[:]
        else:
            return qs

    def filter_queryset(self, qs):
        return qs.filter(name__istartswith=self.query)

    def get(self, request, *args, **kwargs):
        self.query = request.GET.get(self.query_parameter, "")
        object_list = self.get_queryset()
        object_list = self.filter_queryset(object_list)
        object_list = self.limit_queryset(object_list)
        self.object_list = object_list
        allow_empty = self.get_allow_empty()
        if not allow_empty and len(self.object_list) == 0:
            raise Http404(_(u"Empty list and '%(class_name)s.allow_empty' is False.")
                          % {'class_name': self.__class__.__name__})
        context = self.get_context_data(object_list=self.object_list)
        return self.render_to_response(context)

    def json_filter(self, context):
        return [ dict(id=o.id, name=unicode(o)) for o in context['object_list'] ]

    def render_to_response(self, context):
        return self.response_class(
            json.dumps(self.json_filter(context)),
            content_type = "application/json",
        )

