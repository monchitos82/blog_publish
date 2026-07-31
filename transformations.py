import logging

import markdown
from jinja2 import Template
from jinja2.exceptions import TemplateError

from jinja_functions import JinjaFunctions

log = logging.getLogger(__name__)


def parse_template(
    filename: str | None = None,
    content: str | None = None,
    **kwargs,
) -> str:
    """Render a filename template using jinja2."""
    template = None
    rendered_content = ""

    try:
        if filename is not None:
            try:
                with open(filename) as template_file:
                    template = Template(source=template_file.read())
            except OSError as err:
                log.error(f"Could not open the template, error: {err}")
                return ""
        else:
            if not content:
                log.error(
                    "Parse template requires either a filename (preferred) or content"
                )
                return ""
            template = Template(content)

        if template:
            try:
                template.globals.extend(JinjaFunctions.functions)
            except (AttributeError, ValueError) as err:
                log.warning(f"There are no available jinja functions, error: {err}")
            rendered_content = template.render(kwargs)
    except TemplateError as err:
        log.error(f"Failed to render the template {filename}, error: {err}")
    return rendered_content


def render_annotations(
    src: str,
    filename: str,
    header: str,
    footer: str,
    content: str,
    **kwargs,
) -> tuple:
    """Render annotations and transformation for specific filename cases"""
    file_header = header
    file_footer = footer
    file_arguments = kwargs
    split_filename = filename.split("/")

    if filename == f"{src}/index":
        file_arguments["in_main"] = True
        file_footer = parse_template(
            filename=f"{src}/templates/footer.html.j2",
            **file_arguments,
        )
        file_header = parse_template(
            filename=f"{src}/templates/header.html.j2",
            **file_arguments,
        )

    if len(split_filename) == 5:
        year = split_filename[-2]
        # injecting argument to make sure the post goes back to its year index
        file_arguments["year"] = year
        file_arguments["in_post"] = True
        file_footer = parse_template(
            filename=f"{src}/templates/footer.html.j2",
            **file_arguments,
        )

    if content:
        if "<!-- NAV_MAIN -->" in content:
            file_arguments["in_index"] = True
            file_footer = parse_template(
                filename=f"{src}/templates/footer.html.j2",
                **file_arguments,
            )

        if "<!-- NO_PROGRESSBAR -->" in content:
            file_arguments["progressbar"] = False
            file_header = parse_template(
                filename=f"{src}/templates/header.html.j2",
                **file_arguments,
            )
    return (file_header, file_footer)


def parse_markdown(content: str) -> str:
    """Parse a markdown string into HTML."""
    try:
        content = markdown.markdown(
            content,
            extensions=[
                "sane_lists",
                "tables",
            ],
        )
    except (OSError, TypeError, ValueError) as error:
        log.error(f"Failed to parse markdown content, {error}")
        content = ""
    return content


def save_as_html(
    filename: str,
    header: str,
    footer: str,
    content: str,
    replace: dict,
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
                html_file.write(footer)
        except OSError as error:
            log.error(f"Failed to save {html_filename}, error: {error}")
        else:
            save = True
    return save
