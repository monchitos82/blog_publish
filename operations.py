import logging

from files import list_of_files
from transformations import parse_template

log = logging.getLogger(__name__)


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
                html_file.write(f'<main role="main">{content}</main>')
                html_file.write(footer)
        except OSError:
            log.error(f"Failed to save {html_filename}", exc_info=True)
        else:
            save = True
    return save


def extract_post_title(filename: str, title_format: str = "### ") -> str | None:
    """Extract the title of a post based on the H3 header for a markdown file"""
    post_title = None
    try:
        with open(filename) as post_file:
            title = post_file.readline()
        if title_format in title:
            post_title = title.replace(title_format, "").replace("\n", "").strip()
            # if the title is in a markdown comment
            if "]: #" in post_title:
                post_title = post_title.replace("]: #", "").replace("[", "").strip()
    except OSError:
        log.warning("Failed to open post when looking for a title", exc_info=True)
    return post_title


def build_year_index(
    src: str,
    dest: str,
    base_url: str,
    years: list,
    **kwargs,
) -> bool:
    """Create a yearly index of all posts available."""
    for year in years:
        year_content = '<ul class="clean">'
        # the trick here is enable invert to get a desc order by date list of files and then revert the whole list sorted by name
        posts = list_of_files(f"{src}/posts/{year}", clean_extension=False, invert=True)
        if not posts:
            continue
        for post in sorted(
            posts,
            key=lambda f: f.split("/")[-1][:5],
            reverse=True,
        ):
            title = extract_post_title(filename=post)
            if title:
                formatted_filename = post.split("/")[-1].split(".")[0]
                year_content += (
                    f'<li class="clean"><h4><a href="{base_url}/posts/'
                    + f'{year}/{formatted_filename}.html">'
                    + f"{title}</a></h4></li>"
                )
        year_content += "</ul><br/>"

        filename = f"{src}/posts/{year}"
        file_arguments = kwargs
        file_arguments["file_title"] = f"{year}_index"
        file_arguments["file_name"] = f"{year}_index"

        header = parse_template(
            filename=f"{src}/templates/header.html.j2",
            **file_arguments,
        )
        footer = parse_template(
            filename=f"{src}/templates/footer.html.j2",
            **file_arguments,
        )

        if not save_as_html(
            filename=filename,
            header=header,
            footer=footer,
            content=year_content,
            replace={src: dest},
        ):
            log.error(f"Failed to save index file for {year}")
            return False
    return True
