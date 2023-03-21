from django import template

register = template.Library()


@register.filter
def add_class(value, css_class):
    """
    Adds a CSS class to the given value.

    Example usage: {{ my_field|add_class:"form-control" }}
    """
    attrs = value.field.widget.attrs
    attrs["class"] = attrs.get("class", "") + " " + css_class
    return value
