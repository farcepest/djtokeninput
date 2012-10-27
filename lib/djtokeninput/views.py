#!/usr/bin/env python
from itertools import islice

import json
from operator import or_
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.utils.safestring import mark_for_escaping
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from django.views.generic.list import MultipleObjectMixin

class JSONSearchView(MultipleObjectMixin, View):

    query_parameter = "q"
    search_fields = ["^name"]
    min_query_length = 1
    queryset_limit_factor = 10
    queryset_limit_max = 50
    response_class = HttpResponse
    allow_empty = True
    object_permission = None
    user_permission = None

    def get_max_results(self):
        """
        Computes the upper bound for the size of the result set.

        :return:
            Returns the maximum number of results allowed for this particular
            query. This is computed as:

                (length of query string)*(minimum query length)*(queryset
                limit factor)

            i.e. longer query strings allow for a longer result set.
            queryset_limit_max is the absolute upper limit,
            if set to a non-False value. Note that an empty query string (
            length 0) generates a limit of 0.
        :rtype:
            int
        """
        query_length = len(self.query.strip())
        max_results = self.min_query_length*query_length*self.queryset_limit_factor
        if self.queryset_limit_max:
            return min(max_results, self.queryset_limit_max)
        else:
            return max_results

    def limit_queryset(self, qs):
        """
        Apply result size limits to the queryset. get_max_results() is used
        to determine the maximum number of results to return. If
        0/None/False, the entire result set is returned.

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
        Filter the result set based on the query attribute. The search_field
        attribute defines how the search is performed, in the same way that
        is used in the Django admin_. By default, this is ["^name"].
        Override this method if you need more complex behavior.

        _admin: https://docs.djangoproject.com/en/1.4/ref/contrib/admin/#modeladmin-options

        :param qs:
            queryset to filter
        :type qs:
            QuerySet
        :return:
            filtered queryset
        :rtype:
            QuerySet
        """
        # Borrowed from the django admin for compatibility :)
        # Apply keyword searches.
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith('='):
                return "%s__iexact" % field_name[1:]
            elif field_name.startswith('@'):
                return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        orm_lookups = [construct_search(str(search_field))
                        for search_field in self.search_fields]
        for word in self.query.strip().split():
            or_queries = [Q(**{orm_lookup: word})
                          for orm_lookup in orm_lookups]
            qs = qs.filter(reduce(or_, or_queries))
        return qs

    def check_object_perm(self, qs):
        """
        Filters objects for which the user has a certain permission (
        user_permission), if set. This is likely to be relatively expensive.

        :param qs:
            objects to be authorized
        :type qs:
            QuerySet
        :return:
            authorized objects for the user
        :rtype:
            QuerySet
        """
        perm = self.object_permission
        if perm:
            # The queryset at this point has already been filtered by the
            # query string. Since we have to check each object in the
            # queryset for permissions, it seems better to go back to
            # original pre-filtered query, and re-filter based on the object
            # ids of the authorized objects. To avoid checking objects that
            # fall outsize the result size limit, we test the permissions in
            # a generate which is further sliced. It'll slice the queryset
            # after this, but I think that's harmless.
            user = self.request.user
            object_list = ( obj.id for obj in qs if user.has_perm(perm, obj) )
            M = self.get_max_results()
            qs = self.get_queryset().filter(pk__in=islice(object_list, M))
        return qs

    def get(self, request, *args, **kwargs):
        self.query = request.GET.get(self.query_parameter, "")
        perm = self.user_permission
        qs = self.get_queryset()
        if not perm or request.user.has_perm(perm):
            qs = self.filter_queryset(qs)
            qs = self.check_object_perm(qs)
            qs = self.limit_queryset(qs)
        else:
            qs = qs.none()
        self.object_list = qs
        allow_empty = self.get_allow_empty()
        if not allow_empty and len(self.object_list) == 0:
            raise Http404(_(u"Empty list and '%(class_name)s.allow_empty' is False.")
                          % {'class_name': self.__class__.__name__})
        context = self.get_context_data(object_list=self.object_list)
        return self.render_to_response(context)

    def render_object(self, obj):
        """
        Render an object, returning a suitable representation for display in
        the client. By default, the value is escaped. If you need to generate
        raw HTML, override this method.

        :param obj:
            object to render
        :type obj:
            object
        :return:
            rendered object
        :rtype:
            unicode
        """
        return mark_for_escaping(obj)

    def render_objects(self, object_list):
        """
        Filters and converts the context into a sequence of dicts,
        with elements of id and name. id contains the object id. name
        contains rendered version of the object. This value is rendered by
        render_value(). Since these values are being returned to the client
        as part of a JSON stream, you should escape them appropriately. You
        can return HTML, if desired. Only object_list from the context is
        converted by default.

        :param object_list:
            sequence of objects to convert
        :type object_list:
            list(object)
        :return:
            sequence of dicts
        :rtype:
            [dict, ...]
        """
        return [ dict(id=o.id, name=self.render_object(o)) for o in object_list ]

    def render_to_response(self, context):
        """
        Renders the context data (filtered through render_objects()) as a
        JSON response.

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
            json.dumps(self.render_objects(context['object_list'])),
            content_type = "application/json",
        )

