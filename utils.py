import asyncio
import os


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


def load_static_env(src: str, prefix: str = "STATIC") -> dict:
    static = {}
    env_vars = os.environ
    for var in env_vars:
        if prefix in var:
            dirname = "/".join(var.split("_")[1:]).lower()
            print(f"dir: {dirname},")
            if dirname and dirname.replace("/", "") != "":
                var_settings = env_list_as_tuple(var_name=var)
                if var_settings:
                    static[f"{src}/{dirname}"] = var_settings
    return static
