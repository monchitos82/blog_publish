import logging

from datetime import datetime
from feedgen.feed import FeedGenerator
from files import list_of_files
from operations import extract_post_title

log = logging.getLogger(__name__)

def generate_rss_feed(src: str, dest: str, years: list, **settings: dict) -> None: 
    """Generate a feed xml for an RSS feed."""
    try:
        fg = FeedGenerator()
        fg.id(settings.get("site_name", ""))
        fg.title(settings.get("title", ""))
        fg.author({"name": settings.get("author", "")})
        fg.link(href=settings.get("base_url"), rel="alternate")
        fg.subtitle("Updates from my blog")
        fg.language("en")

        print(settings)

        for year in years:
            for post in sorted(
                list_of_files(f"{src}/posts/{year}", clean_extension=False),
                key=lambda f: f.split("/")[-1][:5],
                reverse=True,
            ):
                title = extract_post_title(filename=post)
                # titles are in a format "title text (mm/yy)"
                title_date = title[-7:]
                title_text = title[:-8]
                filename = post.split("/")[-1].split(".")[0]
                title_url = f"{settings.get('base_url')}/posts/{year}/{filename}.html"

                print(title_date, title_text, title_url)

                fe = fg.add_entry()
                fe.id(title)
                fe.title(title_text)
                fe.link(href=title_url)
                fe.pubDate(datetime.strptime(title_date, "(%m/%y)").strftime("%Y-%m-%dT%H:%M:%SZ"))


        fg.rss_file(f"{dest}/feed.xml", pretty=True)
    except (OSError, AttributeError) as error:
        log.error(f"Failed to generate RSS feed: {error}")
