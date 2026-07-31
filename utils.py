import asyncio
import os

PATH_CLEAR_TERMS = (
    " ",
    "(",
    ")",
    "|",
    ":",
    ".",
    ";",
    "&",
    "--",
    "{",
    "[",
    "]",
    "}",
    "$",
    "`",
    "~",
    "%",
    "!",
    "//",
    "\\\\",
)


def env_list_as_tuple(var_name: str, default: tuple | None = None) -> tuple | None:
    env_var = os.getenv(var_name, None)
    if not env_var:
        return default
    split_var = env_var.replace(" ", "").split(",")
    if split_var[-1] == "":
        split_var.pop()
    if not split_var:
        return default
    return tuple(split_var)


async def run_async(tasks: list) -> list:
    # this avoids making main explicitly create an event loop
    return await asyncio.gather(*tasks, return_exceptions=True)


def clean_terms(word: str, terms: tuple | None) -> str:
    if terms:
        for term in terms:
            word = word.replace(term, "")
    return word


def load_static_env(src: str, prefix: str = "STATIC") -> dict:
    static = {}
    env_vars = os.environ
    for var in env_vars:
        if prefix in var:
            dirname = "/".join(var.split("_")[1:]).lower()
            if dirname and dirname.replace("/", "") != "":
                # cleaning up chars that can be used to escape the path or inject vars
                dirname = clean_terms(word=dirname, terms=PATH_CLEAR_TERMS)
                if not dirname:
                    continue
                var_settings = env_list_as_tuple(var_name=var)
                if var_settings:
                    static[f"{src}/{dirname}"] = var_settings
    return static
