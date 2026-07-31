import urllib.parse

from jinja2 import pass_context
from jinja2.runtime import Context


class JinjaFunctions:
    functions = {}

    @classmethod
    def jinja_function(cls, func):
        cls.functions[func.__name__] = func
        return func


@JinjaFunctions.jinja_function
@pass_context
def title_h4_href(context: Context, title: str, date: str, path: str) -> str:
    """
    Render a header using an anchor quick reference format, this generates an h4 header
    with a title anchor and an href anchor.

    Use inside the template:
    {{ title_h4_href('title to the url', 'yyyy-mm-dd', 'name-of-page.html') }}
    """
    base_url = context.get("base_url", "")
    html_title = f"{urllib.parse.quote(title.lower().replace(' ', '_'))}_{date.replace('/', '_')}"
    return (
        f'<span><a name="{html_title}"/></a></span>'
        + '<br class="short"/>'
        + "<h4>"
        + f'<a href="{base_url}/{path}#{html_title}" class="decorated">'
        + f"{title} ({date})"
        + "</a>"
        + "</h4>"
    )
