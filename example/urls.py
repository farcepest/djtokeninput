#!/usr/bin/env python

from django.conf.urls import patterns, url
from example.app.views import home, SearchTags

urlpatterns = patterns("",
  url(r"^$", home, name="home"),
  url(r"^tags$", SearchTags.as_view(), name="search_tags")
)
