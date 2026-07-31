import os

from utils import env_list_as_tuple, run_async
import asyncio


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
    return 'ok'

async def task_b():
    await asyncio.sleep(0.01)
    raise 'failure'

async def task_c():
    await asyncio.sleep(0.01)
    return 'good'


def test_run_async():
    results = asyncio.run(run_async([task_a()]))
    assert results == ['ok']

def test_run_async_fail():
    results = asyncio.run(run_async([task_b()]))
    assert isinstance(results[0], Exception)

def test_run_async_multiple():
    results = asyncio.run(run_async([task_a(), task_c()]))
    assert results == ['ok', 'good']
