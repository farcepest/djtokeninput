#!/usr/bin/env python

from django.shortcuts import render_to_response
from app.forms import ExampleForm
from djtokeninput.views import JSONSearchView
from app.models import Tag


def home(req):
  return render_to_response(
    "index.html", {
      "form": ExampleForm()
    }
  )


class SearchTags(JSONSearchView):

    model = Tag

    def filter_queryset(self, qs, query):
        return qs.filter(name__istartswith=query)

