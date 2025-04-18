from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def menu_active(context, menu):
    view_name = str(context['request'].resolver_match.view_name)
    if view_name.startswith(menu):
        return 'active'
    return ''
