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

@register.filter(name="replace")
def replace(value, args):
    search, replace_with = args.split(',')
    return value.replace(search, replace_with)