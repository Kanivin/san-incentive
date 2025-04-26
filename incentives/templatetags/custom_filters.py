from django import template

register = template.Library()  # Only once!

# rangefilter: generates a list of numbers from start to end
@register.filter
def rangefilter(value):
    try:
        return range(1, int(value) + 1)
    except (ValueError, TypeError):
        return []

# get_item: get value from dictionary using key
@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
