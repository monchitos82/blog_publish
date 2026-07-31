import os

from build_blog import env_list_as_tuple


def test_env_list_as_tuple():
    os.environ["ARG"] = "a, b"
    assert env_list_as_tuple("ARG", None) == ("a", "b")

def test_env_list_as_tuple_invalid_var():
    os.environ["ARG"] = ","
    assert env_list_as_tuple("ARG", None) == ("",)

def test_env_list_as_tuple_single_value():
    os.environ["ARG"] = "abc,"
    assert env_list_as_tuple("ARG", None) == ("abc",)