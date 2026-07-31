import asyncio

from validations import has_broken_anchors


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
