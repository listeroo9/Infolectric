from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def query_replace(context, **kwargs):
    """Return encoded query string with replaced parameters.

    Usage in template:
      ?{% query_replace page=2 %}
      ?{% query_replace page=2 search='fan' %}

    Passing a value of None will remove that parameter.
    """
    request = context.get('request')
    params = {}
    if request is not None:
        # request.GET is immutable QueryDict; make a mutable copy
        params = request.GET.copy()
    else:
        # fallback to empty dict
        params = {}

    for k, v in kwargs.items():
        if v is None:
            params.pop(k, None)
        else:
            params[k] = v

    # Ensure we return a string without leading ?
    try:
        return params.urlencode()
    except Exception:
        # params may be a plain dict
        from urllib.parse import urlencode
        return urlencode(params)
