import logging

import aiofiles
import validators
from bs4 import BeautifulSoup

from files import list_of_files

log = logging.getLogger(__name__)


async def has_broken_anchors(dest: str) -> bool:
    """Find URLs in dest html files and make sure no URL is invalid."""
    for filename in list_of_files(
        dirname=dest, extension="html", clean_extension=False
    ):
        async with aiofiles.open(filename) as f:
            # this operation is expensive, but regexes for anchors would not be better
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
