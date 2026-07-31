import asyncio
from validations import extract_post_title, has_broken_anchors


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


def test_has_broken_anchors_valid_urls(tmp_path):
    f = tmp_path / "page.html"
    f.write_text('<a href="https://example.com">link</a>')
    assert asyncio.run(has_broken_anchors(str(tmp_path))) is False


def test_has_broken_anchors_detects_invalid(tmp_path):
    f = tmp_path / "page.html"
    f.write_text('<a href="not-a-url">bad</a>')
    assert asyncio.run(has_broken_anchors(str(tmp_path))) is True


def test_has_broken_anchors_allows_relative(tmp_path):
    f = tmp_path / "page.html"
    f.write_text('<a href="./local.html">local</a>')
    assert asyncio.run(has_broken_anchors(str(tmp_path))) is False


def test_has_broken_anchors_allows_parent_relative(tmp_path):
    f = tmp_path / "page.html"
    f.write_text('<a href="../other.html">up</a>')
    assert asyncio.run(has_broken_anchors(str(tmp_path))) is False


def test_has_broken_anchors_ignores_hash(tmp_path):
    f = tmp_path / "page.html"
    f.write_text('<a href="#">anchor</a>')
    assert asyncio.run(has_broken_anchors(str(tmp_path))) is False


def test_has_broken_anchors_empty_dir(tmp_path):
    assert asyncio.run(has_broken_anchors(str(tmp_path))) is False
