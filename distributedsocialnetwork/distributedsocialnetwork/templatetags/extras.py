from django import template

# These are custom template filters.
register = template.Library()


@register.filter(name='author_url_converter')
def author_url_converter(value):
    # We take in the value, in this case the url of our author, and then return the one that takes them to the front-facing profile page.
    return value.split('api/')[0] + value.split('api/')[-1]
