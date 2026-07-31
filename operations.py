import logging
import os
import shutil

import aiofiles
import validators
from bs4 import BeautifulSoup

from files import list_of_files
from transformations import parse_markdown_file, render_template, save_as_html

log = logging.getLogger(__name__)


async def has_broken_anchors(dest: str) -> bool:
    """Find URLs in dest html files and make sure no URL is invalid."""
    for filename in list_of_files(
        dirname=dest, extension="html", clean_extension=False
    ):
        async with aiofiles.open(filename) as f:
            content = await f.read()
            soup = BeautifulSoup(content, "html.parser")
            anchors = soup.find_all("a", href=True)
            for anchor in anchors:
                href = anchor.get("href", None)
                if href:
                    if href == "#":
                        continue
                    if not validators.url(href):
                        if href[:2] == "./" or href[:3] == "../":
                            continue
                        log.error(f"invalid anchor: {anchor} in file: {filename}")
                        return True
    return False


def extract_post_title(filename: str) -> str:
    """Extract the title of a post based on the H3 header for a markdown file"""
    try:
        with open(filename) as post_file:
            title = post_file.readline()
        if "###" in title:
            return title.replace("###", "").replace("\n", "").strip()
    except OSError as error:
        log.error(f"Failed to open post when looking for a title: {error}")
    return None


async def build_year_index(
    src: str, dest: str, base_url: str, years: list, header: str, footer: str, tracking_element: str,
) -> bool:
    """Create a yearly index of all posts available."""
    for year in years:
        year_content = "<ul>\n"
        for post in sorted(
            list_of_files(f"{src}/posts/{year}", clean_extension=False),
            key=lambda f: f.split("/")[-1][:5],
            reverse=True
        ):
            title = extract_post_title(filename=post)
            if title:
                formatted_filename = post.split("/")[-1].split(".")[0]
                year_content += (
                    f'    <li><h4><a href="{base_url}/posts/'
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
                tracking_element=tracking_element,

            )
        except OSError as error:
            logging.error(f"Failed to save index file for {year}, {error}")
            return False
    return True
