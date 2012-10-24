#!/usr/bin/env python

import json
from django.http import Http404, HttpResponse
from django.utils.safestring import mark_for_escaping
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
        """
        Apply result size limits to the queryset. get_max_results() is used to determine the maximum
        number of results to return. If 0/None/False, the entire result set is returned.

        :param qs:
            a queryset
        :type qs:
            QuerySet
        :return:
            limited queryset
        :rtype:
            QuerySet
        """
        M = self.get_max_results()
        if M:
            return qs[:M]
        else:
            return qs

    def filter_queryset(self, qs):
        """
        Filter the result set based on the query attribute. By default, this implementation
        uses name__istartswith. Override this method if you need more complex behavior.

        :param qs:
            queryset to filter
        :type qs:
            QuerySet
        :return:
            filtered queryset
        :rtype:
            QuerySet
        """
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

    def render_value(self, value):
        """
        Render an object, returning a suitable representation for display in the client.
        By default, the value is escaped. If you need to generate raw HTML, override this
        method.

        :param value:
            object to render
        :type value:
            object
        :return:
            rendered object
        :rtype:
            unicode
        """
        return mark_for_escaping(value)

    def json_filter(self, context):
        """
        Filters and converts the context into a sequence of dicts, with elements of
        id and name. id contains the object id. name contains rendered version of the
        object. This value is rendered by render_value(). Since these values are being returned
        to the client as part of a JSON stream, you should escape them appropriately. You can
        return HTML, if desired. Only object_list from the context is converted by default.

        :param context:
            template context data
        :type context:
            dict
        :return:
            sequence of dicts
        :rtype:
            [dict, ...]
        """
        return [ dict(id=o.id, name=self.render_value(o)) for o in context['object_list'] ]

    def render_to_response(self, context):
        """
        Renders the context data (filtered through json_filter()) as a JSON response.

        :param context:
            context data
        :type context:
            dict
        :return:
            response
        :rtype:
            HttpResponse
        """
        return self.response_class(
            json.dumps(self.json_filter(context)),
            content_type = "application/json",
        )

