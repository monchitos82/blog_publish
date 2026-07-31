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


def find_last_post(src: str, year: str) -> str:
    """Find which file in the sources is the last one added."""
    existing_files = list_of_files(f"{src}/posts/{year}", clean_extension=False)
    last = None
    for filename in existing_files:
        if not last:
            last = filename
            last_ctime = os.stat(last).st_ctime
        else:
            file_ctime = os.stat(filename).st_ctime
            if last_ctime < file_ctime:
                last = filename
                last_ctime = file_ctime
            elif last_ctime == file_ctime:
                log.warning(
                    f"Two files {last} | {filename} have the same creation timestamp"
                )
    log.info(f"Last file found: {last}")
    return last


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


def get_index_titles(src: str, year: str) -> list:
    """Extract the titles for a year's index"""
    titles = []
    year_index = f"{src}/templates/{year}.md.j2"
    try:
        with open(year_index) as year_index_file:
            soup = BeautifulSoup(year_index_file, "html.parser")
            anchors = soup.find_all("a")
            for anchor in anchors:
                titles.append(anchor.get_text(strip=True))
    except (OSError, AttributeError) as error:
        log.error(f"Failed to extract titles for index of year {year}: {error}")
    return titles


def append_last_title_to_index(src: str, filename: str, year: str) -> bool:
    """Append the last title to year index"""
    year_index = f"{src}/templates/{year}.md.j2"
    backup = f"{year_index}.backup"
    try:
        shutil.copyfile(year_index, backup)
    except (OSError, FileNotFoundError) as error:
        log.error(f"Failed to create backup: {error}")
        return False
    year_index_data = []
    try:
        with open(year_index) as year_index_file:
            # the index is a small file so reading it is safe
            year_index_data = year_index_file.readlines()
        if filename not in ",".join(year_index_data):
            title = extract_post_title(filename=filename)
            # check if the title is new, in case of an update, duplicates are avoided
            if title and title not in get_index_titles(year=year, src=src):
                formatted_filename = filename.split("/")[-1].split(".")[0]
                entry = (
                    '    <li><h3><a href="{{ base_url }}/posts/'
                    + f'{year}/{formatted_filename}.html">'
                    + f"{title}</a></h3></li>\n"
                )
                # making sure it's not appending twice the same line
                if entry != year_index_data[1]:
                    year_index_data.insert(1, entry)
        if year_index_data:
            try:
                with open(year_index, "w+") as f:
                    for line in year_index_data:
                        f.write(line)
            except OSError:
                logging.error(
                    f"Failed to update the year {year} index, a backup was created"
                )
                return False
    except (OSError, ValueError) as error:
        logging.error(f"Failed to open the year {year} index: {error}")
        return False
    os.remove(backup)
    return True


async def build_year_index(
    src: str, dest: str, base_url: str, years: list, header: str, footer: str
) -> bool:
    """Create a yearly index of all posts available."""
    for year in years:
        year_markdown = render_template(
            filename=f"{src}/templates/{year}.md.j2", **{"base_url": base_url}
        )
        try:
            filename = f"{src}/posts/{year}"
            async with aiofiles.open(f"{filename}.md", "w+") as f:
                await f.write(year_markdown)
            save_as_html(
                filename=filename,
                header=header,
                footer=footer,
                content=parse_markdown_file(filename=filename),
                replace={src: dest},
            )
        except OSError as error:
            logging.error(f"Failed to save index file for {year}, {error}")
            return False
    return True
