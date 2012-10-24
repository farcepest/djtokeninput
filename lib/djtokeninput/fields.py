#!/usr/bin/env python

from django import forms
from djtokeninput.widgets import TokenWidget, MultiTokenWidget


class TokenFieldMixIn(object):

    kwargs_for_widget = ("search_view", "search_url", "render_object", "token_limit")

    @staticmethod
    def _class_name(value):
        return value.replace(" ", "-")

    def __init__(self, queryset, *args, **kwargs):
        widget_attrs = {}

        for name in self.kwargs_for_widget:
            if name in kwargs:
                widget_attrs[name] = kwargs.pop(name)

        super(TokenFieldMixIn, self).__init__(queryset, *args, **kwargs)

        for name in widget_attrs:
            setattr(self.widget, name, widget_attrs[name])


class MultiTokenField(TokenFieldMixIn, forms.ModelMultipleChoiceField):

    widget = MultiTokenWidget


class TokenField(TokenFieldMixIn, forms.ModelChoiceField):

    widget = TokenWidget

