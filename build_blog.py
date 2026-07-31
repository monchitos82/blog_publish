"""Publishing script for my blog."""

import argparse
import asyncio
import datetime
import logging
import os

from files import clean_files, copy_dirs, copy_statics, list_of_files
from operations import (append_last_title_to_index, build_year_index,
                        find_last_post, has_broken_anchors)
from transformations import parse_markdown_file, render_template, save_as_html

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

# These are env variables needed for this script to work properly
BASE_URL = os.getenv("BASE_URL", "https://myuser.codeberg.page")
LAST_YEAR = os.getenv("YEAR", str(datetime.datetime.now().year))
YEAR_LOOKBACK = os.getenv("YEAR_LOOKBACK", "1")
SRC = os.getenv("SRC", "../source")
DEST = os.getenv("DEST", "../pages")

# These are directory and extensions that should be copied
STATICS = {
    f"{SRC}": [".txt", ".ico"],
    f"{SRC}/assets": [".css", ".js"],
    f"{SRC}/img": [".png"],
    f"{SRC}/archive": [".json", ".yaml", ".py", ".js", ".log", ".txt"],
}


async def run_asynchronously(tasks: list) -> list:
    results = await asyncio.gather(*tasks)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scan", "-s", help="scan for foul language", action="store_true"
    )
    arguments = parser.parse_args()
    file_errors = False
    base_dirname = SRC
    if not copy_dirs(src=SRC, dest=DEST, depth=1):
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
        },
    )

    # convert all /src markdowns to HTML files and populate /site

    for filename in list_of_files(dirname=base_dirname):
        file_footer = footer
        if "README" in filename:
            continue
        # adding a different footer in the event of creating a post:
        split_filename = filename.split("/")
        if split_filename[-1] != "index":
            if len(split_filename) == 5:
                year = split_filename[-2]
                file_footer = render_template(
                    filename=f"{SRC}/templates/footer.html.j2",
                    **{
                        "base_url": BASE_URL,
                        "year": year,
                        "in_post": True,
                    },
                )
        html_save = save_as_html(
            filename=filename,
            header=header,
            footer=file_footer,
            content=parse_markdown_file(filename=filename),
            replace={SRC: DEST},
        )
        if not html_save:
            log.error(f"File {filename} failed to be generated!")
            file_errors = True
            break

    last_file = find_last_post(src=SRC, year=LAST_YEAR)
    if not last_file:
        log.error(
            "There is a conflict in post creation timestamps, the process will stop"
        )

    year_indexes = None
    YEARS = [LAST_YEAR]

    if append_last_title_to_index(src=SRC, filename=last_file, year=LAST_YEAR):
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
            )
        )

    # if all year indexes are ready we can build the index from them
    if not file_errors and year_indexes:
        broken_anchors, _ = asyncio.run(
            run_asynchronously(
                [
                    has_broken_anchors(dest=f"{DEST}"),
                    clean_files(path=f"{SRC}/posts", extension="md", target=YEARS),
                ]
            )
        )
