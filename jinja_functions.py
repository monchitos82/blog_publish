import urllib.parse

from jinja2 import pass_context
from jinja2.runtime import Context


class JinjaFunctions:
    functions = {}

    @classmethod
    def jinja_function(cls, func) -> object:
        cls.functions[func.__name__] = func
        return func


@JinjaFunctions.jinja_function
@pass_context
def title_h4_href(
    context: Context, title: str, date: str, path: str | None = None
) -> str:
    """
    Render a header using an anchor quick reference format, this generates an h4 header
    with a NAME anchor and an HREF anchor.

    Usage:
    {{ title_h4_href('name of the section', 'yyyy/mm/dd', 'name of the page') }}
    """

    html_title = f"{urllib.parse.quote(title.lower().replace(' ', '_'))}_{date.replace('/', '_')}"
    base_url = context.get("base_url", "")
    if not path:
        path = context.get("path", None)

    print(context)

    decorated_url = ""
    if path and base_url:
        decorated_url = f'<a href="{base_url}/{path}#{html_title}" class="decorated">'

    return (
        f'<span><a name="{html_title}"/></a></span>'
        + '<br class="short"/>'
        + "<h4>"
        + decorated_url
        + f"{title} ({date})"
        + "</a>"
        + "</h4>"
    )
