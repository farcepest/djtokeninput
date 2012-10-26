#!/usr/bin/env python
from django.utils.safestring import mark_for_escaping

import re
import json
import copy
from django import forms
from django.core.urlresolvers import reverse


class TokenWidgetBase(forms.TextInput):

    class Media:
        css = {
            "all": ("css/token-input.css",)
        }

        js = (
            "js/jquery.tokeninput.js",
            "js/djtokeninput.js"
        )

    search_url = None
    search_view = None

    def __init__(self, attrs=None, **kwargs):
        super(TokenWidgetBase, self).__init__(attrs)
        self.settings = self._normalize(kwargs)

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

    @staticmethod
    def _class_name(value):
        return value.replace(" ", "-")

    def render_object(self, obj):
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
        return [ dict(id=o.id, name=self.render_object(o)) for o in object_list ]

    def render(self, name, value, attrs=None):
        settings = copy.copy(self.settings)

        if not self.search_url and self.search_view:
            self.search_url = reverse(self.search_view)
        attrs["data-search-url"] = self.search_url

        attrs["class"] = self._class_name(
            attrs.get("class"), "tokeninput")

        if value or value == 0:
            object_list = self.choices.queryset.filter(pk=value)
            settings["prePopulate"] = self.render_objects(object_list)
        attrs["data-settings"] = json.dumps(settings)
        return super(TokenWidgetBase, self).render(name, value, attrs)

    @staticmethod
    def _class_name(class_name=None, extra=None):
        return " ".join(filter(None, [class_name, extra]))


class TokenWidget(TokenWidgetBase):

    def __init__(self, attrs=None, **kwargs):
        super(TokenWidget, self).__init__(attrs, **kwargs)
        self.settings['tokenLimit'] = 1


class MultiTokenWidget(TokenWidgetBase):

    def value_from_datadict(self, data, files, name):
        values = data.get(name, "").split(",")
        return self.clean_keys(values)

    def clean_keys(self, values):
        return [int(x) for x in values if x.strip().isdigit()]

    def render(self, name, value, attrs=None):
        flat_value = ",".join(map(unicode, value or []))
        settings = copy.copy(self.settings)

        if not self.search_url and self.search_view:
            self.search_url = reverse(self.search_view)
        attrs["data-search-url"] = self.search_url

        attrs["class"] = self._class_name(
            attrs.get("class"), "tokeninput")

        if value is not None:
            object_list = self.choices.queryset.filter(pk__in=value)
            settings["prePopulate"] = self.render_objects(object_list)
        attrs["data-settings"] = json.dumps(settings)
        return super(MultiTokenWidget, self).render(name, flat_value, attrs)
