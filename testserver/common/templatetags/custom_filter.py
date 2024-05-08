from django import template
from django.template.defaultfilters import stringfilter
import math

register = template.Library()

@register.filter(name='div')
def div(value, arg):
    try:
        return int(value) / int(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter(name='mul')
def mul(value, arg):
    return math.ceil(value * arg * 10)/10

@register.filter(name='list_item')
def list_item(_list, index):
    return _list[index]

@register.simple_tag
def make_list(*args):
    return list(args)

@register.filter(name="pop")
def pop(value, prop):
    try:
        value.pop(prop)
    finally:
        return value

@register.filter(name="rule_color")
def rule_color(value):
    if value == '1':
        color = 'success'
    elif value == '2':
        color = 'info'
    elif value == '3':
        color = 'warning'
    elif value == '4':
        color = 'danger'
    else:
        color = 'dark'
    return color

@register.filter(name="get_type")
def get_type(value):
    print(type(value))
    return type(value)
    