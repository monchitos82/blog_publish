import logging

import markdown
from jinja2 import Template
from jinja2.exceptions import TemplateError

log = logging.getLogger(__name__)


def render_template(filename: str, **kwargs) -> str:
    """Render a filename template using jinja2."""
    content = ""
    try:
        with open(filename) as template_file:
            template = Template(source=template_file.read())
            content = template.render(kwargs)
    except OSError as err:
        log.error(f"Could not open the template, error: {err}")
    except TemplateError as err:
        log.error(f"Failed to render the template, error: {err}")
    return content


def parse_markdown(content: str) -> str:
    """Parse a markdown string into HTML."""
    try:
        content = markdown.markdown(
            content,
            output_formats="html5",
            extensions=[
                "smarty",
                "sane_lists",
                "tables",
            ],
        )
    except (OSError, TypeError, ValueError) as error:
        log.error(f"Failed to parse markdown content, {error}")
        content = ""
    return content


def parse_markdown_file(filename: str) -> str:
    """Parse a markdown file into html content."""
    markdown_filename = f"{filename}.md"
    content = None
    try:
        with open(markdown_filename, encoding="utf-8") as markdown_file:
            md_content = markdown_file.read()
            if md_content:
                content = parse_markdown(content=md_content)
    except OSError as error:
        log.error(
            f"failed to generate content from {markdown_filename}, error: {error}"
        )
    return content


def save_as_html(
    filename: str,
    header: str,
    footer: str,
    content: str,
    replace: dict,
    tracking_url: str,
    title: str | None,
) -> bool:
    """Save content as html file."""
    html_filename = filename
    for item in replace:
        html_filename = f"{html_filename.replace(item, replace[item])}"
    html_filename += ".html"
    save = False
    if content:
        log.info(f"Saving {filename} as {html_filename}")
        try:
            with open(html_filename, "w+", encoding="utf-8") as html_file:
                html_file.write(header)
                html_file.write(f'\n    <main role="main">\n{content}\n    </main>\n')
                # on build this will have the ./src prefix, cleaning it up
                if tracking_url:
                    no_path_filename = ("/").join(html_filename.split("/")[2:])
                    tracking_element = f'\n    <img style="display:none;" src="{tracking_url}/count?p=/{no_path_filename}">\n'
                    if title is not None:
                        tracking_element = f'\n    <img style="display:none;" src="{tracking_url}/count?p=/{no_path_filename}&t={title}">\n'
                    html_file.write(tracking_element)
                html_file.write(footer)
        except OSError as error:
            log.error(f"Failed to save {html_filename}, error: {error}")
        else:
            save = True
    return save
