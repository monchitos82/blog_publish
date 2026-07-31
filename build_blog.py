"""Publishing script for my blog."""

import asyncio
import datetime
import logging
import os

from files import async_clean_files, clean_files, copy_dirs, copy_statics, list_of_files
from operations import build_year_index, extract_post_title
from rss import generate_rss_feed
from transformations import (
    parse_markdown_file,
    render_annotations,
    render_content_as_template,
    render_template,
    save_as_html,
)
from utils import env_list_as_tuple, load_static_env, run_async
from validations import has_broken_anchors

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

# These are env variables needed for this script to work properly
BASE_URL = os.getenv("BASE_URL", "")
LAST_YEAR = os.getenv("YEAR", str(datetime.datetime.now().year))
YEAR_LOOKBACK = os.getenv("YEAR_LOOKBACK", "1")
SRC = os.getenv("SRC", "../source")
DEST = os.getenv("DEST", "../site")
TRACKING = os.getenv("TRACKING", "")
TITLE = os.getenv("TITLE", "")
AUTHOR = os.getenv("AUTHOR", "")
EMAIL = os.getenv("EMAIL", "")
SITE_NAME = os.getenv("SITE_NAME", "")

if __name__ == "__main__":
    file_errors = False

    # this is used to signal where to copy files and which extensions to use
    STATICS = {
        f"{SRC}": env_list_as_tuple("STATICS_BASE", (".txt")),
    }

    STATICS.update(load_static_env(src=SRC))

    clean_files(path=f"{DEST}", extension="html")

    # first step is to clean-up the page files

    if not copy_dirs(src=SRC, dest=DEST, depth=2):
        file_errors = True
    if not copy_statics(src=SRC, dest=DEST, statics=STATICS):
        file_errors = True

    year_indexes = None
    last_year = int(LAST_YEAR)
    first_year = last_year - int(YEAR_LOOKBACK)
    YEARS = [str(year) for year in range(first_year, last_year + 1)]

    arguments = {
        "author": AUTHOR,
        "base_url": BASE_URL,
        "in_es": False,
        "in_index": False,
        "in_main": False,
        "in_post": False,
        "progressbar": True,
        "menu": None,
        "title": TITLE,
        "tracking_url": TRACKING,
        "year": None,
        "years": YEARS,
    }

    menu = render_template(
        filename=f"{SRC}/templates/menu.html.j2",
        **arguments,
    )
    arguments["menu"] = menu

    header = render_template(
        filename=f"{SRC}/templates/header.html.j2",
        **arguments,
    )
    footer = render_template(
        filename=f"{SRC}/templates/footer.html.j2",
        **arguments,
    )

    # convert all /src markdowns to HTML files and populate /site
    for filename in list_of_files(dirname=SRC):
        split_filename = filename.split("/")
        if "README" in filename or split_filename[-1].startswith("."):
            continue

        content = parse_markdown_file(filename=filename)
        file_arguments = dict(arguments)
        file_header, file_footer = render_annotations(
            src=SRC,
            filename=filename,
            header=header,
            footer=footer,
            content=content,
            **file_arguments,
        )

        if "<!-- NO_RENDER -->" not in content:
            content = render_content_as_template(
                content=content,
                **{
                    "base_url": BASE_URL,
                },
            )

        html_save = save_as_html(
            filename=filename,
            header=file_header,
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

    file_arguments = dict(arguments)
    file_arguments["progressbar"] = False
    file_arguments["in_index"] = True
    index_header = render_template(
        filename=f"{SRC}/templates/header.html.j2",
        **file_arguments,
    )
    index_footer = render_template(
        filename=f"{SRC}/templates/footer.html.j2",
        **file_arguments,
    )
    year_indexes = build_year_index(
        src=SRC,
        dest=DEST,
        base_url=BASE_URL,
        years=YEARS,
        header=index_header,
        footer=index_footer,
        tracking_url=TRACKING,
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
                site_title=TITLE,
            ):
                log.warning("The RSS feed could not be generated")

    elif file_errors:
        log.critical(
            "The build cannot continue, there are file errors making the build inconsistent"
        )
    elif not year_indexes:
        log.critical("Year indexes were not built, the build navigation will be broken")
