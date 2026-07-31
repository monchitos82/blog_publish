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
    render_content_as_template,
    render_template,
    save_as_html,
)
from utils import env_list_as_tuple, run_async
from validations import has_broken_anchors

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
TITLE = os.getenv("TITLE", None)
AUTHOR = os.getenv("AUTHOR", None)
EMAIL = os.getenv("EMAIL", None)
ACCOUNT = os.getenv("ACCOUNT", None)

if __name__ == "__main__":
    file_errors = False
    base_dirname = SRC

    STATICS = {
        f"{SRC}": env_list_as_tuple("STATICS_BASE", (".txt", ".css")),
        f"{SRC}/img": env_list_as_tuple("STATICS_IMG", (".png", ".svg", ".ico")),
        f"{SRC}/misc": env_list_as_tuple("STATICS_MISC", (".html", ".json")),
        f"{SRC}/static": env_list_as_tuple("STATICS_STATIC", (".txt",)),
    }

    (clean_files(path=f"{DEST}", extension="html"),)

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
    for filename in list_of_files(dirname=base_dirname):
        file_header = header
        file_footer = footer
        split_filename = filename.split("/")
        if "README" in filename or split_filename[-1].startswith("."):
            continue

        content = parse_markdown_file(filename=filename)
        file_arguments = dict(arguments)

        if filename == f"{SRC}/index":
            # base, index.md at root
            file_arguments["in_main"] = True
            file_footer = render_template(
                filename=f"{SRC}/templates/footer.html.j2",
                **file_arguments,
            )
            file_header = render_template(
                filename=f"{SRC}/templates/header.html.j2",
                **file_arguments,
            )
        if len(split_filename) == 5:
            year = split_filename[-2]
            file_arguments["year"] = year
            file_arguments["in_post"] = True
            file_footer = render_template(
                filename=f"{SRC}/templates/footer.html.j2",
                **file_arguments,
            )

        if "<!-- NAV_MAIN -->" in content:
            file_arguments["in_index"] = True
            file_footer = render_template(
                filename=f"{SRC}/templates/footer.html.j2",
                **file_arguments,
            )

        if "<!-- NO_PROGRESSBAR -->" in content:
            file_arguments["progressbar"] = False
            file_header = render_template(
                filename=f"{SRC}/templates/header.html.j2",
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
                site_name=ACCOUNT,
                site_title=TITLE,
            ):
                log.warning("The RSS feed could not be generated")

    elif file_errors:
        log.critical(
            "The build cannot continue, there are file errors making the build inconsistent"
        )
    elif not year_indexes:
        log.critical("Year indexes were not built, the build navigation will be broken")
