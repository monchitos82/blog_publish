from operations import build_year_index, extract_post_title, save_as_html


def test_extract_post_title_returns_title(tmp_path):
    f = tmp_path / "post.md"
    f.write_text("### My Great Post\nsome content")
    assert extract_post_title(str(f)) == "My Great Post"


def test_extract_post_title_wrong_heading_returns_none(tmp_path):
    f = tmp_path / "post.md"
    f.write_text("# Not H3\nsome content")
    assert extract_post_title(str(f)) is None


def test_extract_post_title_missing_file_returns_none():
    assert extract_post_title("/nonexistent/post.md") is None


def test_extract_post_title_strips_whitespace(tmp_path):
    f = tmp_path / "post.md"
    f.write_text("###   Padded Title   \n")
    assert extract_post_title(str(f)) == "Padded Title"


def test_build_year_index_creates_index(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    posts = src / "posts" / "2026"
    dest_posts = dest / "posts" / "2026"
    posts.mkdir(parents=True)
    dest_posts.mkdir(parents=True)
    (dest / "posts").mkdir(exist_ok=True)

    post = posts / "01_01_my-post.md"
    post.write_text("### My Post (01/01)\nHello")

    result = build_year_index(
        src=str(src),
        dest=str(dest),
        base_url="https://example.com",
        years=["2026"],
        header="<header/>",
        footer="<footer/>",
    )
    assert result is True
    index = dest / "posts" / "2026.html"
    assert index.exists()
    content = index.read_text()
    assert "My Post" in content
    assert "https://example.com/posts/2026" in content


def test_build_year_index_empty_year(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    (src / "posts" / "2026").mkdir(parents=True)
    (dest / "posts").mkdir(parents=True)

    result = build_year_index(
        src=str(src),
        dest=str(dest),
        base_url="https://example.com",
        years=["2026"],
        header="",
        footer="",
    )
    assert result is True


def test_build_year_index_skips_posts_without_h3_title(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    posts = src / "posts" / "2026"
    posts.mkdir(parents=True)
    (dest / "posts").mkdir(parents=True)

    (posts / "01_01_no-title.md").write_text("## Bad title")

    build_year_index(
        src=str(src),
        dest=str(dest),
        base_url="https://example.com",
        years=["2026"],
        header="",
        footer="",
    )
    content = (dest / "posts" / "2026.html").read_text()
    assert "no-title" not in content


def test_save_as_html_creates_file(tmp_path):
    filename = str(tmp_path / "page")
    result = save_as_html(
        filename=filename,
        header="<header/>",
        footer="<footer/>",
        content="<p>hello</p>",
        replace={},
    )
    assert result is True
    assert (tmp_path / "page.html").exists()


def test_save_as_html_applies_replace(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()
    dest.mkdir()
    filename = str(src / "page")
    save_as_html(
        filename=filename,
        header="",
        footer="",
        content="<p>hi</p>",
        replace={str(src): str(dest)},
    )
    assert (dest / "page.html").exists()


def test_save_as_html_empty_content_returns_false(tmp_path):
    result = save_as_html(
        filename=str(tmp_path / "page"),
        header="",
        footer="",
        content="",
        replace={},
    )
    assert result is False


def test_save_as_html_writes_header_and_footer(tmp_path):
    filename = str(tmp_path / "page")
    save_as_html(
        filename=filename,
        header="<HEADER>",
        footer="<FOOTER>",
        content="<p>body</p>",
        replace={},
    )
    content = (tmp_path / "page.html").read_text()
    assert content.startswith("<HEADER>")
    assert content.endswith("<FOOTER>")
