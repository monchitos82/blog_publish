import os

import pytest
from jinja2 import Environment, FunctionLoader

from jinja_functions import JinjaFunctions
from transformations import (
    parse_markdown,
    parse_template,
    render_annotations,
)


@pytest.fixture
def jinja_env():
    env = Environment(loader=FunctionLoader(lambda name: ""))
    env.globals.update(JinjaFunctions.functions)
    return env


def test_parse_template_renders_variables(tmp_path):
    t = tmp_path / "tmpl.j2"
    t.write_text("Hello {{ name }}!")
    assert parse_template(filename=t, name="world") == "Hello world!"


def test_parse_template_missing_file_returns_empty():
    assert parse_template("/nonexistent/template.j2") == ""


def test_parse_template_no_variables(tmp_path):
    t = tmp_path / "tmpl.j2"
    t.write_text("<html/>")
    assert parse_template(filename=t) == "<html/>"


def test_parse_template_with_content():
    content = "{{ foo }}"
    assert parse_template(content=content, foo="var") == "var"


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
    arguments = {"in_post": False}
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
