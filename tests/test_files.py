import asyncio
import os
from unittest.mock import patch

from files import (async_clean_files, clean_files, copy_dirs, copy_statics,
                   list_of_files, load_file_content)


def test_load_file_content(tmp_path):
    src = tmp_path / "a.md"
    src.write_text("foo")
    content = load_file_content(filename=src, extension=".md")
    assert content == "foo"

def test_load_file_content_too_large(tmp_path):
    src = tmp_path / "a.md"
    src.write_text("foo bar")
    content = load_file_content(filename=src, limit=1, extension=".md")
    assert content is None


def test_list_of_files_finds_by_extension(tmp_path):
    (tmp_path / "post.md").write_text("hello")
    (tmp_path / "main.css").write_text("body{}")
    result = list_of_files(str(tmp_path), extension="md", clean_extension=False)
    assert any("post.md" in f for f in result)
    assert not any("main.css" in f for f in result)


def test_list_of_files_clean_extension_strips_suffix(tmp_path):
    (tmp_path / "post.md").write_text("hello")
    result = list_of_files(str(tmp_path), extension="md", clean_extension=True)
    assert any(f.endswith("post") for f in result)


def test_list_of_files_excludes_venv(tmp_path):
    venv_dir = tmp_path / "venv"
    venv_dir.mkdir()
    (venv_dir / "readme.md").write_text("venv file")
    result = list_of_files(str(tmp_path), extension="md", clean_extension=False)
    assert not any("venv" in f for f in result)


def test_list_of_files_wildcard_includes_all(tmp_path):
    (tmp_path / "a.md").write_text("")
    (tmp_path / "b.css").write_text("")
    (tmp_path / "c.js").write_text("")
    result = list_of_files(str(tmp_path), extension="*", clean_extension=False)
    names = [os.path.basename(f) for f in result]
    assert "a.md" in names
    assert "b.css" in names
    assert "c.js" in names


def test_list_of_files_recursive(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "nested.md").write_text("nested")
    result = list_of_files(str(tmp_path), extension="md", clean_extension=False)
    assert any("nested.md" in f for f in result)


def test_list_of_files_ignores_dotfiles(tmp_path):
    (tmp_path / ".hidden.md").write_text("hidden")
    result = list_of_files(str(tmp_path), extension="md", clean_extension=False)
    assert any(".hidden.md" in f for f in result)


def test_list_of_files_empty_dir(tmp_path):
    result = list_of_files(str(tmp_path), extension="md")
    assert result == []


def test_copy_dirs_mirrors_structure(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()
    dest.mkdir()
    (src / "posts").mkdir()
    (src / "style").mkdir()
    assert copy_dirs(str(src), str(dest)) is True
    assert (dest / "posts").is_dir()
    assert (dest / "style").is_dir()


def test_copy_dirs_skips_dotfiles(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()
    dest.mkdir()
    (src / ".hidden").mkdir()
    copy_dirs(str(src), str(dest))
    assert not (dest / ".hidden").exists()


def test_copy_dirs_depth_recursive(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()
    dest.mkdir()
    (src / "posts" / "2026").mkdir(parents=True)
    assert copy_dirs(str(src), str(dest), depth=2) is True
    assert (dest / "posts" / "2026").is_dir()


def test_copy_dirs_depth_zero_no_recursion(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()
    dest.mkdir()
    (src / "posts" / "2026").mkdir(parents=True)
    copy_dirs(str(src), str(dest), depth=0)
    assert (dest / "posts").is_dir()
    assert not (dest / "posts" / "2026").exists()


def test_copy_dirs_returns_false_on_bad_src(tmp_path):
    result = copy_dirs(str(tmp_path / "nonexistent"), str(tmp_path / "dest"))
    assert result is False


def test_copy_dirs_tolerates_existing_dir(tmp_path):
    src = tmp_path / "src"
    dest = tmp_path / "dest"
    src.mkdir()
    dest.mkdir()
    (src / "posts").mkdir()
    (dest / "posts").mkdir()
    assert copy_dirs(str(src), str(dest)) is True


def test_copy_statics_copies_matching_files(tmp_path):
    src = tmp_path / "src"
    style = src / "style"
    style.mkdir(parents=True)
    (style / "main.css").write_text("body{}")
    (style / "main.txt").write_text("foo")
    dest = tmp_path / "dest"
    dest_ = dest / "style"
    dest_.mkdir(parents=True)
    statics = {str(style): [".css"]}
    result = copy_statics(str(src), str(dest), statics)
    assert result is True
    assert (dest_ / "main.css").exists()
    assert not (dest_ / "main.txt").exists()


def test_copy_statics_wildcard(tmp_path):
    src = tmp_path / "src"
    temporary = src / "temporary"
    temporary.mkdir(parents=True)
    (temporary / "demo.html").write_text("<html/>")
    dest = tmp_path / "dest"
    dest_temporary = dest / "temporary"
    dest_temporary.mkdir(parents=True)
    statics = {str(temporary): ["*"]}
    result = copy_statics(str(src), str(dest), statics)
    assert result is True
    assert (dest_temporary / "demo.html").exists()


def test_clean_files_deletes_by_extension(tmp_path):
    f = tmp_path / "page.html"
    f.write_text("<html/>")
    assert clean_files(str(tmp_path), "html") is True
    assert not f.exists()


def test_clean_files_preserves_keep_files(tmp_path):
    keep = tmp_path / "important.keep.html"
    keep.write_text("<html/>")
    clean_files(str(tmp_path), "html")
    assert keep.exists()


def test_clean_files_targeted_deletes_only_matching(tmp_path):
    target_file = tmp_path / "2026.html"
    other_file = tmp_path / "about.html"
    target_file.write_text("")
    other_file.write_text("")
    clean_files(str(tmp_path), "html", target=["2026"])
    assert not target_file.exists()
    assert other_file.exists()


def test_clean_files_keep_prefix(tmp_path):
    preserved = tmp_path / "keep_this.html"
    removed = tmp_path / "remove_this.html"
    preserved.write_text("")
    removed.write_text("")
    clean_files(str(tmp_path), "html", keep_prefix=str(tmp_path / "keep"))
    assert preserved.exists()
    assert not removed.exists()


def test_clean_files_returns_false_on_oserror(tmp_path):
    f = tmp_path / "page.html"
    f.write_text("")
    with patch("files.os.remove", side_effect=OSError("permission denied")):
        result = clean_files(str(tmp_path), "html")
    assert result is False


def test_clean_files_returns_true_when_nothing_to_delete(tmp_path):
    assert clean_files(str(tmp_path), "html") is True


def test_async_clean_files_delegates(tmp_path):
    f = tmp_path / "page.html"
    f.write_text("")
    result = asyncio.run(async_clean_files(str(tmp_path), "html"))
    assert result is True
    assert not f.exists()
