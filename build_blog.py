"""Publishing script for my blog."""

import asyncio
import datetime
import logging
import os
import sys

from files import (
    async_clean_files,
    clean_files,
    copy_dirs,
    copy_statics,
    list_of_files,
    load_file_content,
)
from operations import build_year_index, extract_post_title, save_as_html
from rss import generate_rss_feed
from transformations import (
    parse_markdown,
    parse_template,
    render_annotations,
)
from utils import load_static_env, run_async
from validations import has_broken_anchors

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

# These are env variables needed for this script to work properly
BASE_URL = os.getenv("BASE_URL", "")
TRACKING_URL = os.getenv("TRACKING_URL", "")
YEAR = os.getenv("YEAR", str(datetime.datetime.now().year))
FIRST_YEAR = os.getenv("FIRST_YEAR", str(datetime.datetime.now().year - 1))
SRC = os.getenv("SRC", "../source")
DEST = os.getenv("DEST", "../site")
AUTHOR = os.getenv("AUTHOR", "")
EMAIL = os.getenv("EMAIL", "")
SITE_NAME = os.getenv("SITE_NAME", "")
SITE_TITLE = os.getenv("SITE_TITLE", "")

if __name__ == "__main__":
    file_errors = False

    # this is used to signal where to copy files and which extensions to use
    STATICS = {
        f"{SRC}": (".txt",),
    }

    STATICS.update(load_static_env(src=SRC))

    clean_files(path=f"{DEST}", extension="html")

    # first step is to clean-up the page files

    if not copy_dirs(src=SRC, dest=DEST, depth=2):
        file_errors = True
    if not copy_statics(src=SRC, dest=DEST, statics=STATICS):
        file_errors = True

    year_indexes = None
    YEARS = [str(year) for year in range(int(FIRST_YEAR), int(YEAR) + 1)]

    arguments = {
        "author": AUTHOR,
        "base_url": BASE_URL,
        "tracking_url": TRACKING_URL,
        "file_name": None,
        "file_title": None,
        "in_index": False,
        "in_main": False,
        "in_post": False,
        "progressbar": True,
        "menu": None,
        "post_year": None,
        "years": YEARS,
        "title": SITE_TITLE,
    }

    arguments["menu"] = parse_template(
        filename=f"{SRC}/templates/menu.html.j2",
        **arguments,
    )

    # convert all /src markdowns to HTML files and populate /site
    markdown_files = list_of_files(dirname=SRC)
    if markdown_files:
        for filename in markdown_files:
            split_filename = filename.split("/")
            file_name = split_filename[-1]
            if file_name == "README" or file_name.startswith("."):
                continue

            raw_content = load_file_content(filename=f"{filename}.md")
            if not raw_content:
                continue

            content = parse_markdown(content=raw_content)
            if not content:
                continue

            file_arguments = dict(arguments)
            file_title = extract_post_title(filename=f"{filename}.md")
            if file_title:
                file_arguments["file_title"] = file_title
            if file_name:
                file_arguments["file_name"] = file_name

            file_header, file_footer = render_annotations(
                src=SRC,
                filename=filename,
                content=content,
                **file_arguments,
            )
            if not file_header or not file_footer:
                if not file_header:
                    log.error(
                        f"Document {filename} structure failed to render at header transformation"
                    )
                if not file_footer:
                    log.error(
                        f"Document {filename} structure failed to render at footer transformation"
                    )
                continue

            # using NO_RENDER bypasses the jinja rendering on the content
            if "<!-- NO_RENDER -->" not in content:
                content = parse_template(
                    content=content,
                    **file_arguments,
                )
                if not content:
                    continue

            html_save = save_as_html(
                filename=filename,
                header=file_header,
                footer=file_footer,
                content=content,
                replace={SRC: DEST},
            )
            if not html_save:
                log.error(f"File {filename} failed to be generated!")
                file_errors = True
                break

    # build the indexes from the posts in /src
    index_arguments = dict(arguments)
    index_arguments["progressbar"] = False
    index_arguments["in_index"] = True
    index_arguments["file_title"] = ""
    index_arguments["file_name"] = ""

    year_indexes = build_year_index(
        src=SRC,
        dest=DEST,
        **index_arguments,
    )

    # if all year indexes are ready we can build the index from them
    if not file_errors and year_indexes:
        tasks = [
            has_broken_anchors(dest=f"{DEST}"),
            async_clean_files(path=f"{SRC}/posts", extension="md", target=YEARS),
            async_clean_files(path=f"{SRC}/posts", extension="html", target=YEARS),
        ]
        for result in asyncio.run(run_async(tasks)):
            if isinstance(result, Exception):
                log.error(f"A task failed with an exception: {result}")

        # once indexes are ready, update the RSS if enabled
        update_rss = os.getenv("UPDATE_RSS", None)
        if update_rss:
            log.info("RSS updates enabled")
            if not generate_rss_feed(
                src=SRC,
                dest=DEST,
                years=YEARS,
                author=AUTHOR,
                email=EMAIL,
                base_url=BASE_URL,
                site_name=SITE_NAME,
                site_title=SITE_TITLE,
            ):
                log.warning("The RSS feed could not be generated")

    elif file_errors:
        log.critical(
            "The build process cannot continue, there are file errors making the site inconsistent"
        )
        sys.exit(1)
    elif not year_indexes:
        log.critical("Year indexes were not built, the site navigation will be broken")
        sys.exit(1)
