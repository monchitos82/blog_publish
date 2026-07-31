from rss import generate_rss_feed

def test_generate_rss(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    posts = src / "posts" / "2026"
    dest_posts = dest / "posts" / "2026"
    posts.mkdir(parents=True)
    dest_posts.mkdir(parents=True)
    (dest / "posts").mkdir(exist_ok=True)

    post = posts / "01_01_my-post.md"
    post.write_text("### My Post (01/01)\nHello")

    result = generate_rss_feed(
        src=str(src),
        dest=str(dest),
        years=["2026"],
        author="some author",
        email="email@example.com",
        base_url="https://example.com",
        site_name="some site",
        site_title="some title",
    )
    assert result is True
    feed = dest / "atom.xml"
    assert feed.exists()
    content = feed.read_text()
    assert "My Post" in content
