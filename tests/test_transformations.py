import os

import pytest
from jinja2 import Environment, FunctionLoader
from transformations import (parse_markdown, render_annotations,
                             render_content_as_template, render_template,
                             save_as_html, title_h4_href)


@pytest.fixture
def jinja_env():
    env = Environment(loader=FunctionLoader(lambda name: ""))
    env.globals["title_h4_href"] = title_h4_href
    return env


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


def test_title_h4_href_with_real_context(jinja_env):
    template = jinja_env.from_string("{{ title_h4_href(title, date, path) }}")
    context_data = {"base_url": "https://example.com"}
    render_context = {
        **context_data,
        "title": "foo bar",
        "date": "10/10/2026",
        "path": "foobar.html",
    }
    result = template.render(render_context)
    expect = """
    <h4>
      <a name="foo_bar_10_10_2026" href="https://example.com/foobar.html#foo_bar_10_10_2026">
        foo bar (10/10/2026)
      </a>
    </h4>
    """
    assert result == expect


import os


def test_render_annotations_index():
    src = f"{os.getcwd()}/tests"
    header = ""
    footer = ""
    content = ""
    filename = f"{src}/index"
    arguments = {"in_main": False}
    _, file_footer = render_annotations(
        src=src,
        header=header,
        footer=footer,
        content=content,
        filename=filename,
        **arguments,
    )
    assert '"in_main": True' in file_footer


def test_render_annotations_in_post():
    src = f"{os.getcwd()}/tests"
    header = ""
    footer = ""
    content = ""
    filename = "foo/bar/posts/2026/foobar"
    arguments = {"in_post": False, "year": "2000"}
    _, file_footer = render_annotations(
        src=src,
        header=header,
        footer=footer,
        content=content,
        filename=filename,
        **arguments,
    )
    assert '"in_post": True' in file_footer
    assert '"year": 2026' in file_footer


def test_render_annotations_nav_main():
    src = f"{os.getcwd()}/tests"
    header = ""
    footer = ""
    content = "<!-- NAV_MAIN -->"
    filename = "foo"
    arguments = {"in_main": False, "in_index": False}
    _, file_footer = render_annotations(
        src=src,
        header=header,
        footer=footer,
        content=content,
        filename=filename,
        **arguments,
    )
    assert '"in_main": False' in file_footer
    assert '"in_index": True' in file_footer


def test_render_annotations_nav_main_es():
    src = f"{os.getcwd()}/tests"
    header = ""
    footer = ""
    content = "<!-- NAV_MAIN_ES -->"
    filename = "foo"
    arguments = {"in_main": False, "in_index": False, "in_es": False}
    _, file_footer = render_annotations(
        src=src,
        header=header,
        footer=footer,
        content=content,
        filename=filename,
        **arguments,
    )
    assert '"in_main": False' in file_footer
    assert '"in_index": True' in file_footer
    assert '"in_es": True' in file_footer


def test_render_annotations_progressbar():
    src = f"{os.getcwd()}/tests"
    header = ""
    footer = ""
    content = "<!-- NO_PROGRESSBAR -->"
    filename = "foo"
    arguments = {"progressbar": True}
    file_header, _ = render_annotations(
        src=src,
        header=header,
        footer=footer,
        content=content,
        filename=filename,
        **arguments,
    )
    assert '"progressbar": False' in file_header
