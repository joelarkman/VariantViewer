from django import template

register = template.Library()


@register.filter
def get_display_choice(choices, key):
    return [x[1] for x in choices if x[0] == key][0]
