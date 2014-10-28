# -*- coding: utf-8 -*-

from django import forms

class PostForm(forms.Form):
    postText = forms.CharField(widget=forms.Textarea, required=True, max_length="500", label="")

