import logging
import urllib.parse

import markdown
from jinja2 import Template, pass_context
from jinja2.exceptions import TemplateError

log = logging.getLogger(__name__)


@pass_context
def title_h4_href(context: dict, title: str, date: str, path: str) -> str:
    log.info(f"Title is: {title} and path is: {path}")
    base_url = context.get("base_url")
    html_title = f"{urllib.parse.quote(title)}_{date.replace('/', '_')}"
    return f"""
      <h4>
        <a name=\"{html_title}\" href=\"{base_url}/{path}#{html_title}\">
          {title.replace("_", " ").title()} ({date})
        </a>
      </h4>
    """


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


def render_content_as_template(content: str, **kwargs) -> str:
    """Render content as a template using jinja2 (no file used here)."""
    try:
        template_as_content = Template(content)
        template_as_content.globals["title_h4_href"] = title_h4_href
        content = template_as_content.render(kwargs)
    except TemplateError as err:
        log.error(f"Failed to render the content as template, error: {err}")
    return content


def render_annotations(
    src: str, filename: str, header: str, footer: str, content: str, **kwargs
) -> tuple:
    """Render annotations and transformation for specific filename cases"""
    file_header = header
    file_footer = footer
    file_arguments = kwargs
    split_filename = filename.split("/")

    if filename == f"{src}/index":
        # base, index.md at root
        file_arguments["in_main"] = True
        file_footer = render_template(
            filename=f"{src}/templates/footer.html.j2",
            **file_arguments,
        )
        file_header = render_template(
            filename=f"{src}/templates/header.html.j2",
            **file_arguments,
        )
    if len(split_filename) == 5:
        year = split_filename[-2]
        file_arguments["year"] = year
        file_arguments["in_post"] = True
        file_footer = render_template(
            filename=f"{src}/templates/footer.html.j2",
            **file_arguments,
        )

    if "<!-- NAV_MAIN -->" in content:
        file_arguments["in_index"] = True
        file_footer = render_template(
            filename=f"{src}/templates/footer.html.j2",
            **file_arguments,
        )

    if "<!-- NAV_MAIN_ES -->" in content:
        file_arguments["in_index"] = True
        file_arguments["in_es"] = True
        file_footer = render_template(
            filename=f"{src}/templates/footer.html.j2",
            **file_arguments,
        )

    if "<!-- NO_PROGRESSBAR -->" in content:
        file_arguments["progressbar"] = False
        file_header = render_template(
            filename=f"{src}/templates/header.html.j2",
            **file_arguments,
        )
    return (file_header, file_footer)


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
