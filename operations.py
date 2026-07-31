import logging

from files import list_of_files
from transformations import save_as_html

log = logging.getLogger(__name__)


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
    except OSError as error:
        log.warning(f"Failed to open post when looking for a title: {error}")
    return post_title


def build_year_index(
    src: str,
    dest: str,
    base_url: str,
    years: list,
    header: str,
    footer: str,
) -> bool:
    """Create a yearly index of all posts available."""
    for year in years:
        year_content = '<ul class="clean">\n'
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
                    f'    <li class="clean"><h4><a href="{base_url}/posts/'
                    + f'{year}/{formatted_filename}.html">'
                    + f"{title}</a></h4></li>\n"
                )
        year_content += "</ul>\n"
        year_content += "<br/>\n"

        filename = f"{src}/posts/{year}"
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
