# custom_filters.py

from django import template

register = template.Library()

# rangefilter: generates a list of numbers from start to end
@register.filter
def rangefilter(value):
    try:
        return range(1, int(value) + 1)
    except ValueError:
        return []
