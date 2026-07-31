import logging
from datetime import datetime

from feedgen.feed import FeedGenerator

from files import list_of_files
from operations import extract_post_title

log = logging.getLogger(__name__)


def generate_rss_feed(
    src: str,
    dest: str,
    years: list,
    author: str,
    base_url: str,
    email: str,
    site_name: str,
    site_title: str,
) -> bool:
    """Generate a feed xml for an RSS feed."""
    try:
        fg = FeedGenerator()
        fg.id(site_name)
        fg.title(site_title)
        fg.author({"name": f"{author}", "email": f"{email}"})
        fg.link(href="f{base_url}", rel="alternate")
        fg.logo(f"{base_url}/img/favicon.ico")
        fg.subtitle(f"{author} blog updates")
        fg.link(href=f"{base_url}/atom.xml", rel="self")
        fg.language("en")
        fg.generator(generator="blog generator", version="0.1", uri="undefined")

        for year in years:
            for post in sorted(
                list_of_files(f"{src}/posts/{year}", clean_extension=False),
                key=lambda f: f.split("/")[-1][:5],
            ):
                if "index" in post:
                    continue
                title = extract_post_title(filename=post)
                # titles are in a format "title text (mm/yy)"
                title_text, title_date = None, None
                if title and len(title) > 8:
                    title_date = title[-7:]
                    title_text = title[:-8]
                filename = post.split("/")[-1].split(".")[0]
                title_url = f"{base_url}/posts/{year}/{filename}.html"

                if title_text and title_date and title_url:
                    fe = fg.add_entry()
                    fe.id(title)
                    fe.title(title_text)
                    fe.link(href=title_url)
                    fe.pubDate(
                        datetime.strptime(title_date, "(%m/%y)").strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        )
                    )

        fg.rss_file(f"{dest}/atom.xml")
    except (OSError, AttributeError) as error:
        log.error(f"Failed to generate RSS feed: {error}")
        return False
    return True
