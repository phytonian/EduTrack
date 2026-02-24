"""
EduTrack Template Extras
Place this file at:
  core/templatetags/dict_extras.py

Also make sure core/templatetags/__init__.py exists (even if empty).
Load in templates with: {% load dict_extras %}
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get a value from a dict by key in Django templates.
    Usage: {{ my_dict|get_item:key_variable }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
