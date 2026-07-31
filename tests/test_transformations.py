import os

from transformations import render_template, render_content_as_template, parse_markdown, parse_markdown_file, save_as_html


def test_render_template_renders_variables(tmp_path):
    t = tmp_path / "tmpl.j2"
    t.write_text("Hello {{ name }}!")
    assert render_template(str(t), name="world") == "Hello world!"


def test_render_template_missing_file_returns_empty():
    assert render_template("/nonexistent/template.j2") == ""


def test_render_template_no_variables(tmp_path):
    t = tmp_path / "tmpl.j2"
    t.write_text("<html/>")
    assert render_template(str(t)) == "<html/>"


def test_render_content_as_template():
    content = "{{ foo }}"
    assert render_content_as_template(content, foo="var") == "var"


def test_parse_markdown_basic():
    result = parse_markdown("# Hello")
    assert "<h1>" in result


def test_parse_markdown_table():
    md = "| a | b |\n|---|---|\n| 1 | 2 |"
    result = parse_markdown(md)
    assert "<table>" in result


def test_parse_markdown_empty_string():
    result = parse_markdown("")
    assert result == ""


def test_parse_markdown_file_reads_and_parses(tmp_path):
    f = tmp_path / "post.md"
    f.write_text("### My Post\nHello world")
    result = parse_markdown_file(str(tmp_path / "post"))
    assert "<h3>" in result


def test_parse_markdown_file_missing_returns_none(tmp_path):
    result = parse_markdown_file(str(tmp_path / "nonexistent"))
    assert result is None


def test_parse_markdown_file_empty_returns_none(tmp_path):
    f = tmp_path / "empty.md"
    f.write_text("")
    result = parse_markdown_file(str(tmp_path / "empty"))
    assert result is None


def test_save_as_html_creates_file(tmp_path):
    filename = str(tmp_path / "page")
    result = save_as_html(
        filename=filename,
        header="<header/>",
        footer="<footer/>",
        content="<p>hello</p>",
        replace={},
        tracking_url=None,
        title=None,
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
        tracking_url=None,
        title=None,
    )
    assert (dest / "page.html").exists()


def test_save_as_html_empty_content_returns_false(tmp_path):
    result = save_as_html(
        filename=str(tmp_path / "page"),
        header="",
        footer="",
        content="",
        replace={},
        tracking_url=None,
        title=None,
    )
    assert result is False


def test_save_as_html_tracking_url_no_title(tmp_path):
    filename = str(tmp_path / "a" / "b" / "page")
    os.makedirs(str(tmp_path / "a" / "b"))
    save_as_html(
        filename=filename,
        header="",
        footer="",
        content="<p>x</p>",
        replace={},
        tracking_url="https://track.example.com",
        title=None,
    )
    content = (tmp_path / "a" / "b" / "page.html").read_text()
    assert "track.example.com/count?p=" in content
    assert "&t=" not in content


def test_save_as_html_tracking_url_with_title(tmp_path):
    filename = str(tmp_path / "a" / "b" / "page")
    os.makedirs(str(tmp_path / "a" / "b"))
    save_as_html(
        filename=filename,
        header="",
        footer="",
        content="<p>x</p>",
        replace={},
        tracking_url="https://track.example.com",
        title="My Post",
    )
    content = (tmp_path / "a" / "b" / "page.html").read_text()
    assert "&t=My Post" in content


def test_save_as_html_writes_header_and_footer(tmp_path):
    filename = str(tmp_path / "page")
    save_as_html(
        filename=filename,
        header="<HEADER>",
        footer="<FOOTER>",
        content="<p>body</p>",
        replace={},
        tracking_url=None,
        title=None,
    )
    content = (tmp_path / "page.html").read_text()
    assert content.startswith("<HEADER>")
    assert content.endswith("<FOOTER>")
