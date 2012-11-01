#!/usr/bin/env python
from django.utils.safestring import mark_for_escaping, mark_safe

import re
import json
import copy
from django import forms
from django.core.urlresolvers import reverse


class unescaped(object):

    def __init__(self, thing):
        self._thing = thing

    def __repr__(self):
        return "unescaped(%s)" % repr(self._thing)

    def __iter__(self):
        return iter(self._thing)


class SettingsEncoder(json.JSONEncoder):

    def _iterencode_default(self, o, markers=None):
        if isinstance(o, unescaped):
            return o
        newobj = self.default(o)
        return self._iterencode(newobj, markers)


class TokenWidgetBase(forms.TextInput):

    class Media:
        css = {
            "all": ("css/token-input.css",)
        }

        js = (
            "js/jquery.tokeninput.js",
        )

    search_url = None
    search_view = None
    render_object = None
    default_on_create = unescaped("""
    function(data){
        var input = this.data("tokenInputObject");
        var S = $(this).data("settings")
        var C = S.jsonContainer;
        data['csrfmiddlewaretoken'] = $('input[name="csrfmiddlewaretoken"]').val();
        return $.post(S.url, data,
            function(results){input.add((C?results[C]:results)[0]);}); }""")

    def __init__(self, attrs=None, **kwargs):
        super(TokenWidgetBase, self).__init__(attrs)
        self.settings = self._normalize(kwargs)
        if "jsonContainer" not in self.settings:
            self.settings["jsonContainer"] = "object_list"
        if self.settings.get("allowCreation", False) \
            and "onCreate" not in self.settings:
            self.settings["onCreate"] = self.default_on_create

    @classmethod
    def _normalize(cls, settings):
        """
        Return a copy of `settings` (a dict) with any underscored keys replaced
        with camelCased keys. Useful for passing Python-style dicts to Tokeninput,
        which expects strange camelCase dicts.
        """

        return dict([
        (cls._camelcase(key), val)
        for key, val in settings.items()
        ])

    @staticmethod
    def _camelcase(s):
        return re.sub("_(.)", lambda m: m.group(1).capitalize(), s)

    def default_render_object(self, obj):
        """
        Render an object, returning a suitable representation for display in the client.
        By default, the value is escaped. If you need to generate raw HTML, override this
        method.

        :param obj:
            object to render
        :type obj:
            object
        :return:
            rendered object
        :rtype:
            unicode
        """
        if self.render_object:
            return self.render_object(obj)
        return mark_for_escaping(obj)

    def render_objects(self, object_list):
        """
        Filters and converts the context into a sequence of dicts, with elements of
        id and name. id contains the object id. name contains rendered version of the
        object. This value is rendered by render_value(). Since these values are being returned
        to the client as part of a HTML document, you should escape them appropriately.

        :param object_list:
            sequence of objects to convert
        :type object_list:
            list(object)
        :return:
            sequence of dicts
        :rtype:
            [dict, ...]
        """
        render = self.render_object or self.default_render_object
        return [ dict(id=o.pk, name=render(o)) for o in object_list ]


class TokenWidget(TokenWidgetBase):

    def __init__(self, attrs=None, **kwargs):
        super(TokenWidget, self).__init__(attrs, **kwargs)
        self.settings['tokenLimit'] = 1

    def prepopulate(self, value):
        if value:
            object_list = self.choices.queryset.filter(pk=value)
        else:
            object_list = self.choices.queryset.none()
        return object_list

    def render(self, name, value, attrs=None):
        settings = copy.copy(self.settings)
        if not self.search_url and self.search_view:
            self.search_url = reverse(self.search_view)
        settings["prePopulate"] = self.render_objects(self.prepopulate(value))
        script = """<script type="text/javascript">$(document).ready(""" \
        """function(){$("#%s").tokenInput("%s",%s);});</script>""" % (
            attrs['id'],
            self.search_url,
            SettingsEncoder().encode(settings),
        )
        elem = super(TokenWidget, self).render(name, value, attrs)
        return elem + mark_safe(script)


class MultiTokenWidget(TokenWidgetBase):

    def value_from_datadict(self, data, files, name):
        values = data.get(name, "").split(",")
        return self.clean_keys(values)

    def clean_keys(self, values):
        return [int(x) for x in values if x.strip().isdigit()]

    def prepopulate(self, value):
        if value is not None:
            object_list = self.choices.queryset.filter(pk__in=value)
        else:
            object_list = self.choices.queryset.none()
        return object_list

    def render(self, name, value, attrs=None):
        flat_value = ",".join(map(unicode, value or []))
        settings = copy.copy(self.settings)
        if not self.search_url and self.search_view:
            self.search_url = reverse(self.search_view)
        settings["prePopulate"] = self.render_objects(self.prepopulate(value))
        script = """<script type="text/javascript">$(document).ready(""" \
        """function(){$("#%s").tokenInput("%s",%s);});</script>""" % (
            attrs['id'],
            self.search_url,
            SettingsEncoder().encode(settings),
            )
        elem = super(MultiTokenWidget, self).render(name, flat_value, attrs)
        return elem + mark_safe(script)