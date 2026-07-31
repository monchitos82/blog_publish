import asyncio
from operations import build_year_index

def test_build_year_index_creates_index(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    posts = src / "posts" / "2026"
    dest_posts = dest / "posts" / "2026"
    posts.mkdir(parents=True)
    dest_posts.mkdir(parents=True)
    (dest / "posts").mkdir(exist_ok=True)

    post = posts / "01_01_my-post.md"
    post.write_text("### My Post\nHello")

    result = asyncio.run(build_year_index(
        src=str(src),
        dest=str(dest),
        base_url="https://example.com",
        years=["2026"],
        header="<header/>",
        footer="<footer/>",
        tracking_url=None,
    ))
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

    result = asyncio.run(build_year_index(
        src=str(src),
        dest=str(dest),
        base_url="https://example.com",
        years=["2026"],
        header="",
        footer="",
        tracking_url=None,
    ))
    assert result is True


def test_build_year_index_skips_posts_without_h3_title(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    posts = src / "posts" / "2026"
    posts.mkdir(parents=True)
    (dest / "posts").mkdir(parents=True)

    (posts / "01_01_no-title.md").write_text("## Bad title")

    asyncio.run(build_year_index(
        src=str(src),
        dest=str(dest),
        base_url="https://example.com",
        years=["2026"],
        header="",
        footer="",
        tracking_url=None,
    ))
    content = (dest / "posts" / "2026.html").read_text()
    assert "no-title" not in content