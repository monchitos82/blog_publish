import asyncio
import os

import pytest
from utils import (PATH_CLEAR_TERMS, clean_terms, env_list_as_tuple,
                   load_static_env, run_async)


def test_env_list_as_tuple():
    os.environ["ARG"] = "a, b"
    assert env_list_as_tuple("ARG", None) == ("a", "b")


def test_env_list_as_tuple_invalid_var():
    os.environ["ARG"] = ","
    assert env_list_as_tuple("ARG", None) == ("",)


def test_env_list_as_tuple_single_value():
    os.environ["ARG"] = "abc,"
    assert env_list_as_tuple("ARG", None) == ("abc",)


async def task_a():
    await asyncio.sleep(0.01)
    return "ok"


async def task_b():
    await asyncio.sleep(0.01)
    raise Exception("failure")


async def task_c():
    await asyncio.sleep(0.01)
    return "good"


def test_run_async():
    results = asyncio.run(run_async([task_a()]))
    assert results == ["ok"]


def test_run_async_fail():
    results = asyncio.run(run_async([task_b()]))
    assert isinstance(results[0], Exception)


def test_run_async_multiple():
    results = asyncio.run(run_async([task_a(), task_c()]))
    assert results == ["ok", "good"]


def test_load_static_env():
    os.environ["STATIC-TST_TEST_1"] = "a, b"
    os.environ["STATIC-TST_TEST2"] = "*"
    os.environ["STATIC-tst_TEST3"] = "x"
    src = "base"
    static = load_static_env(src=src, prefix="STATIC-TST")
    del os.environ["STATIC-TST_TEST_1"]
    del os.environ["STATIC-TST_TEST2"]
    del os.environ["STATIC-tst_TEST3"]
    expected = {
        f"{src}/test/1": ("a", "b"),
        f"{src}/test2": ("*",),
    }
    assert static == expected


def test_load_static_env_bad_env():
    os.environ["STATIC-TST_"] = "a, b"
    src = "base"
    static = load_static_env(src=src, prefix="STATIC-TST")
    del os.environ["STATIC-TST_"]
    assert static == {}


def test_load_static_env_relative():
    os.environ["STATIC-TST<_.._.._ETC"] = "a, b"
    src = "base"
    static = load_static_env(src=src, prefix="STATIC-TST")
    del os.environ["STATIC-TST<_.._.._ETC"]
    assert static == {
        "base/etc": (
            "a",
            "b",
        )
    }


words = [(":(){ :|:& };:", ""), ("/../etc/", "etc/"), ("${SOMETHING}@", "SOMETHING@")]


@pytest.mark.parametrize("word, result", words)
def test_clean_terms(word, result):
    assert clean_terms(word=word, terms=PATH_CLEAR_TERMS) == result
