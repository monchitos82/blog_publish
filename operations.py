import logging

from files import list_of_files
from transformations import save_as_html
from validations import extract_post_title

log = logging.getLogger(__name__)


async def build_year_index(
    src: str, dest: str, base_url: str, years: list, header: str, footer: str, tracking_url: str,
) -> bool:
    """Create a yearly index of all posts available."""
    for year in years:
        year_content = f'<ul class="clean">\n'
        for post in sorted(
            list_of_files(f"{src}/posts/{year}", clean_extension=False),
            key=lambda f: f.split("/")[-1][:5],
            reverse=True
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
        try:
            filename = f"{src}/posts/{year}"
            save_as_html(
                filename=filename,
                header=header,
                footer=footer,
                content=year_content,
                replace={src: dest},
                tracking_url=tracking_url,
                title=f'{year} index',
            )
        except OSError as error:
            logging.error(f"Failed to save index file for {year}, {error}")
            return False
    return True
