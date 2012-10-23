#!/usr/bin/env python

from django import forms
from djtokeninput.fields import TokenField
from app import models


class ExampleForm(forms.Form):
  title = forms.CharField()
  desc = forms.CharField(widget=forms.Textarea)
  tags = TokenField(models.Tag, required=False, search_view="search_tags")
