#!/usr/bin/env python

from django import forms
from djtokeninput.fields import TokenField, MultiTokenField
from app import models


class ExampleForm(forms.Form):
  title = forms.CharField()
  desc = forms.CharField(widget=forms.Textarea)
  tags = MultiTokenField(models.Tag.objects.all(), required=False, search_view="search_tags")
  show = TokenField(models.Tag.objects.all(), required=False, search_url="http://shell.loopj.com/tokeninput/tvshows.php")
  # the definition for show works by virtue of not saving the form
