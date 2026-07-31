"""Publishing script for my blog."""

import asyncio
import datetime
import logging
import os

from files import (async_clean_files, clean_files, copy_dirs, copy_statics,
                   list_of_files)
from operations import build_year_index
from transformations import parse_markdown_file, render_template, save_as_html
from validations import has_broken_anchors, extract_post_title

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

# These are env variables needed for this script to work properly
BASE_URL = os.getenv("BASE_URL", None)
LAST_YEAR = os.getenv("YEAR", str(datetime.datetime.now().year))
YEAR_LOOKBACK = os.getenv("YEAR_LOOKBACK", "1")
SRC = os.getenv("SRC", "../source")
DEST = os.getenv("DEST", "../site")
TRACKING = os.getenv("TRACKING", None)

# These are directory and extensions that should be copied
STATICS = {
    f"{SRC}": [".txt", ".ico"],
    f"{SRC}/assets": [".css", ".js"],
    f"{SRC}/img": [".png", ".jpeg", ".svg"],
    f"{SRC}/archive": [".json", ".yaml", ".py", ".rb", ".go", ".js", ".log", ".txt"],
    f"{SRC}/experiments": ["*"],
}


async def run_asynchronously(tasks: list) -> list:
    results = await asyncio.gather(*tasks)
    return results


if __name__ == "__main__":

    file_errors = False
    base_dirname = SRC

    clean_files(path=f"{DEST}", extension="html"),

    # first step is to clean-up the page files

    if not copy_dirs(src=SRC, dest=DEST, depth=2):
        file_errors = True
    copy_statics(src=SRC, dest=DEST, statics=STATICS)

    # get the base of every page ready by setting header, menu and footer
    menu = render_template(
        filename=f"{SRC}/templates/menu.html.j2",
        **{
            "base_url": BASE_URL,
        },
    )
    header = render_template(
        filename=f"{SRC}/templates/header.html.j2",
        **{
            "base_url": BASE_URL,
            "menu": menu,
        },
    )
    footer = render_template(
        filename=f"{SRC}/templates/footer.html.j2",
        **{
            "base_url": BASE_URL,
            "in_post": False,
            "in_index": False,
            "in_main": False,
        },
    )

    index_pages = ('index', 'about', 'notes')

    # convert all /src markdowns to HTML files and populate /site
    for filename in list_of_files(dirname=base_dirname):
        file_footer = footer
        split_filename = filename.split("/")
        if "README" in filename or split_filename[-1].startswith("."):
            continue

        content = parse_markdown_file(filename=filename)

        if filename == f'{SRC}/index':
            # base, index.md at root
            file_footer = render_template(
                filename=f"{SRC}/templates/footer.html.j2",
                **{
                    "base_url": BASE_URL,
                    "tracking_url": TRACKING,
                    "in_main": True,
                },
            )
        elif split_filename[-1] in index_pages:
            # other pages at root
            file_footer = render_template(
                filename=f"{SRC}/templates/footer.html.j2",
                **{
                    "base_url": BASE_URL,
                    "in_index": True,
                },
            )
        elif split_filename[-1] not in index_pages:
            # posts will point back to their year index in the footer
            if len(split_filename) == 5:
                year = split_filename[-2]
                page = split_filename[-1]
                file_footer = render_template(
                    filename=f"{SRC}/templates/footer.html.j2",
                    **{
                        "base_url": BASE_URL,
                        "year": year,
                        "in_post": True,
                        "page_name": f"{page}"
                    },
                )
                
        html_save = save_as_html(
            filename=filename,
            header=header,
            footer=file_footer,
            content=content,
            replace={SRC: DEST},
            tracking_url=TRACKING,
            title=extract_post_title(f"{filename}.md"),
        )
        if not html_save:
            log.error(f"File {filename} failed to be generated!")
            file_errors = True
            break

    year_indexes = None
    last_year = int(LAST_YEAR)
    first_year = last_year - int(YEAR_LOOKBACK)
    YEARS = [str(year) for year in range(first_year, last_year + 1)]
    index_footer = render_template(
        filename=f"{SRC}/templates/footer.html.j2",
        **{
            "base_url": BASE_URL,
            "in_index": True,
        },
    )
    year_indexes = asyncio.run(
        build_year_index(
            src=SRC,
            dest=DEST,
            base_url=BASE_URL,
            years=YEARS,
            header=header,
            footer=index_footer,
            tracking_url=TRACKING,
        )
    )

    # if all year indexes are ready we can build the index from them
    if not file_errors and year_indexes:
        broken_anchors, _, _ = asyncio.run(
            run_asynchronously(
                [
                    has_broken_anchors(dest=f"{DEST}"),
                    async_clean_files(
                        path=f"{SRC}/posts", extension="md", target=YEARS
                    ),
                    async_clean_files(
                        path=f"{SRC}/posts", extension="html", target=YEARS
                    ),
                ]
            )
        )
