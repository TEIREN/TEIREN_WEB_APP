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
    if str(value) == '1':
        color = 'success'
    elif str(value) == '2':
        color = 'info'
    elif str(value) == '3':
        color = 'warning'
    elif str(value) == '4':
        color = 'danger'
    else:
        color = 'dark'
    return color

@register.filter(name="get_type")
def get_type(value):
    return type(value)


@register.filter(name="get_item")
def get_item(_dict, _key):
    return _dict.get(_key, '')


@register.simple_tag
def page_range(page_number, max_page_number):
    start_page = max(int(page_number)-5, 1)
    end_page = min(int(page_number)+5, max_page_number)
    return range(start_page, end_page+1)