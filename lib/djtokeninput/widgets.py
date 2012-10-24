#!/usr/bin/env python

import re
import json
import copy
from django import forms
from django.core.urlresolvers import reverse


class TokenWidget(forms.TextInput):

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
        super(TokenWidget, self).__init__(attrs)
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

    def render_value(self, value):
        return unicode(value)

    def render(self, name, value, attrs=None):
        flat_value = ",".join(map(unicode, value or []))
        settings = copy.copy(self.settings)

        if not self.search_url and self.search_view:
            self.search_url = reverse(self.search_view)
        attrs["data-search-url"] = self.search_url

        attrs["class"] = self._class_name(
            attrs.get("class"), "tokeninput")

        if value is not None:
            settings["prePopulate"] = [
                {"id": pk, "name": self.render_value(self.choices.queryset.get(pk=pk))}
              for pk in value
            ]

        attrs["data-settings"] = json.dumps(settings)
        return super(TokenWidget, self).render(name, flat_value, attrs)

    @staticmethod
    def _class_name(class_name=None, extra=None):
        return " ".join(filter(None, [class_name, extra]))

    def value_from_datadict(self, data, files, name):
        values = data.get(name, "").split(",")
        return self.clean_keys(values)

    def clean_keys(self, values):
        return [int(x) for x in values if x.strip().isdigit()]
