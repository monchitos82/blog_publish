"""Publishing script for my blog."""

import argparse
import asyncio
import datetime
import json
import logging
import os
import shutil
import sys

import aiofiles
import markdown
import validators
from bs4 import BeautifulSoup
from jinja2 import Template
from jinja2.exceptions import TemplateError
from dataclasses import dataclass

log = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
log.setLevel(logging.DEBUG)
log.addHandler(console_handler)

AUTO = os.getenv("AUTO", False)
BASE_URL = os.getenv("BASE_URL", "https://myuser.codeberg.page")

LOCATIONS = {"posts": True, "landing": False}
CURSING = ["fuck", "asshole"]
YEARS = ["2024", "2025", "2026"]

SRC = os.getenv("SRC", "../source")
DEST = os.getenv("DEST", "../pages")

# These are directory and extensions that should be copied, the rest is ignored
STATICS = {
    f"{SRC}": [".txt", ".ico"],
    f"{SRC}/assets": [".css", ".js"],
    f"{SRC}/img": [".png"],
}

def render_template(filename: str, **kwargs) -> str:
    """Render a filename template using jinja2."""
    content = ""
    try:
        with open(filename) as f:
            template = Template(source=f.read())
            content = template.render(kwargs)
    except OSError as err:
        log.error(f"Could not open the template, error: {err}")
    except TemplateError as err:
        log.error(f"Failed to render the template, error: {err}")
    return content


def list_of_files(dirname: str, extension: str = "md", clean_extension=True) -> list:
    """Generate a list of files having an [extension] structure."""
    files_list = []

    for root, _, files in os.walk(dirname):
        for file_ in files:
            # venv may contain markdown files, we need to ignore those
            if "venv" not in root and (file_.endswith(extension) or extension == "*"):
                if clean_extension:
                    files_list.append(
                        os.path.join(root, ".".join(file_.split(".")[:-1]))
                    )
                else:
                    files_list.append(os.path.join(root, file_))
    return files_list


def copy_dirs(src: str = SRC, dest: str = DEST, depth=0) -> bool:
    """Mirror the structure of directories within a src path (1 level non-recursive)."""
    try:
        for item in os.listdir(src):
            if os.path.isdir(os.path.join(src, item)):
                # added some recursion after splitting posts, ideally 1 level depth max
                if depth:
                    copy_dirs(
                        src=os.path.join(src, item),
                        dest=os.path.join(dest, item),
                        depth=(depth - 1),
                    )
                try:
                    os.mkdir(f"{dest}/{item}")
                except FileExistsError:
                    # this may be acceptable, especially if the dir already exists
                    pass
                except OSError as error:
                    # other errors should be addressed
                    log.error(f"Creation of directory {item} failed, error: {error}")
                    return False
    except OSError as error:
        log.error(f"Access to {src} failed, error: {error}")
        return False
    return True


def copy_statics(statics: list, src: str = SRC, dest: str = DEST) -> None:
    """Copy any static files, this runs independently of markdown rendering."""
    for item in statics:
        site = item.replace(src, dest)
        for extension in statics[item]:
            files = list_of_files(
                dirname=item, extension=extension, clean_extension=False
            )
            for filename in files:
                try:
                    shutil.copy2(src=filename, dst=site)
                except OSError as error:
                    log.error(f"Copy of static file {filename} failed, error: {error}")


def parse_markdown(content: str) -> str:
    """Parse a markdown string into HTML."""
    try:
        content = markdown.markdown(
            content,
            output_formats="html5",
            extensions=[
                "smarty",
                "sane_lists",
                "tables",
            ],
        )
    except (OSError, TypeError, ValueError) as error:
        log.error(f"Failed to parse markdown content, {error}")
        content = ""
    return content


def parse_markdown_file(filename: str) -> str:
    """Parse a markdown file into html content."""
    markdown_file = f"{filename}.md"
    content = None
    try:
        with open(markdown_file, encoding="utf-8") as f:
            md_content = f.read()
            if md_content:
                content = parse_markdown(content=md_content)
    except OSError as error:
        log.error(f"failed to generate content from {markdown_file}, error: {error}")
    return content


def save_as_html(
    filename: str, header: str, footer: str, content: str, replace: dict
) -> bool:
    """Save content as html file."""
    html_file = filename
    for item in replace:
        html_file = f"{html_file.replace(item, replace[item])}"
    html_file += ".html"
    save = False
    if content:
        log.info(f"Saving {filename} as {html_file}")
        try:
            with open(html_file, "w+", encoding="utf-8") as f:
                f.write(header)
                f.write(f"\n    <main role=\"main\">\n{content}\n    </main>\n")
                f.write(footer)
        except OSError as error:
            log.error(f"Failed to save {html_file}, error: {error}")
        else:
            save = True
    return save


async def build_year_index(
    years: list, header: str, footer: str, src: str = SRC, dest: str = DEST
) -> bool:
    """Create a yearly index of all posts available."""
    for year in years:
        year_markdown = render_template(
            filename=f"{src}/templates/{year}.md.j2", **{"base_url": BASE_URL}
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
            log.error(f"Failed to save index file for {year}, {error}")
            return False
    return True


async def has_foul_language(dest: str = DEST, extension: str = "html") -> bool:
    """Scan the rendered docs looking for foul language."""
    clean = True
    files = list_of_files(dirname=dest, extension=extension, clean_extension=False)
    for filename in files:
        async with aiofiles.open(filename) as f:
            content = await f.read()
            for word in CURSING:
                if word.lower() in str(content).lower():
                    log.warning(f"'{word}' found in {filename}")
                    clean = False
    return clean


async def has_broken_anchors(dest: str = DEST) -> bool:
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


def find_last_post(year: str, src: str = SRC) -> str:
    """Find which file in the sources is the last one added."""
    existing_files = list_of_files(f"{src}/posts/{year}", clean_extension=False)
    last = None
    last_time = None
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
                log.warning(f"Two files {last} | {filename} have the same creation timestamp")
    log.info(f"Last file found: {last}")
    return last


def extract_post_title(filename: str) -> str:
    """Extract the title of a post based on the H3 header for a markdown file"""
    try:
        with open(filename) as f:
            title = f.readline()
        if "###" in title:
            return title.replace("###", "").replace("\n", "").strip()
    except OSError as error:
        log.error(f"Failed to open post when looking for a title: {error}")
    return None


def get_index_titles(year: str, src: str = SRC) -> list:
    """Extract the titles for a year's index"""
    titles = []
    year_index = f"{src}/templates/{year}.md.j2"
    try:
        with open(year_index) as f:
            soup = BeautifulSoup(f, "html.parser")
            anchors = soup.find_all("a")
            for anchor in anchors:
                titles.append(anchor.get_text(strip=True))
    except (OSError, AttributeError) as error:
        log.error(f"Failed to extract titles for index of year {year}: {error}")
    return titles


def append_last_title_to_index(filename: str, year: str, src: str = SRC) -> bool:
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
        with open(year_index) as f:
            # the index is a small file so reading it is safe
            year_index_data = f.readlines()
        if filename not in ','.join(year_index_data):
            title = extract_post_title(filename=filename)
            # check if the title is new, in case of an update, duplicates are avoided
            if title and title not in get_index_titles(year=year, src=src):
                formatted_filename = filename.split("/")[-1].split(".")[0]
                entry = ("    <li><h3><a href=\"{{ base_url }}/posts/" +
                        f"{year}/{formatted_filename}.html\">" +
                        f"{title}</a></h3></li>\n")
                # making sure it's not appending twice the same line
                if entry != year_index_data[1]:
                    year_index_data.insert(1, entry)
        if year_index_data:
            try:
                with open(year_index, "w+") as f:
                    for line in year_index_data:
                        f.write(line)
            except OSError:
                log.error(f"Failed to update the year {year} index, a backup was created")
                return False
    except (OSError, ValueError) as error:
        log.error(f"Failed to open the year {year} index: {error}")
        return False
    os.remove(backup)
    return True

async def run_asynchronously(tasks: list) -> list:
    results = await asyncio.gather(*tasks)
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", "-s", help="scan for cursing", action="store_true")
    arguments = parser.parse_args()
    file_errors = False
    base_dirname = SRC
    if not copy_dirs(depth=1):
        file_errors = True
    copy_statics(statics=STATICS)

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
            "locations": json.dumps(LOCATIONS),
        },
    )
    footer = render_template(
        filename=f"{SRC}/templates/footer.html.j2",
        **{"base_url": BASE_URL},
    )

    # convert all /src markdowns to HTML files and populate /site
        
    for filename in list_of_files(dirname=base_dirname):
        if "README" in filename:
            continue
        html_save = save_as_html(
            filename=filename,
            header=header,
            footer=footer,
            content=parse_markdown_file(filename=filename),
            replace={SRC: DEST},
        )
        if "gobble" in filename:
            html_save = save_as_html(
                filename=filename,
                header="",
                footer="",
                content=parse_markdown_file(filename=filename),
                replace={SRC: DEST},
            )

        if not html_save:
            log.error(f"File {filename} failed to be generated!")
            file_errors = True
            break

    last_file = (find_last_post(year=YEARS[-1], src=SRC))
    if not last_file:
        log.error("There is a conflict in post creation timestamps, the process will stop")
        #sys.exit(1)
    
    year_indexes = None

    if append_last_title_to_index(filename=last_file, year=YEARS[-1]):
        year_indexes = asyncio.run(build_year_index(years=YEARS, header=header, footer=footer))

    # if all year indexes are ready we can build the index from them
    if not file_errors and year_indexes:
        foul_language, broken_anchors = asyncio.run(run_asynchronously(
            [
                has_foul_language(),
                has_broken_anchors(dest=f"{DEST}")
            ]
        ))

        if arguments.scan and not foul_language:
            log.info("Cursing found in the results, do you want to continue? [Y/n]")
            response = "N"
            if not AUTO:
                response = input()
            if not response:
                response = "y"
            if response.lower() != "y":
                sys.exit(1)

