from django import template

register = template.Library()

@register.filter
def has_any_permission(permissions, value):
    try:
        module, action = [s.strip() for s in value.split(",")]
        return permissions.get((module, action), False)
    except ValueError:
        return False
