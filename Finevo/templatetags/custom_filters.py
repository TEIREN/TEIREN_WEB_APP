from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    original, new = arg.split(',')
    return value.replace(original, new)

@register.filter(name='has_image_extension')
def has_image_extension(value):
    image_extensions = ['.jpg', '.jpeg', '.png']
    return any(value.lower().endswith(ext) for ext in image_extensions)