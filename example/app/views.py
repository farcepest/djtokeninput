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

    queryset = Tag.objects.all()



