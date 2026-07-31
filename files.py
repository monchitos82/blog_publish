import logging
import os
import shutil

log = logging.getLogger(__name__)


def list_of_files(dirname: str, extension: str = "md", clean_extension=True) -> list:
    """Generate a list of files having an [extension]."""
    files_list = []

    for root, _, files in os.walk(dirname):
        for file_ in files:
            # venv may contain markdown files, we need to ignore those
            if "venv" not in root and (file_.endswith(extension) or extension == "*"):
                if clean_extension:
                    files_list.append(
                        os.path.join(root, ".".join(file_.split(".")[:-1]))
                    )
                else:
                    files_list.append(os.path.join(root, file_))
    return files_list


def copy_dirs(src: str, dest: str, depth=0) -> bool:
    """Mirror the structure of directories within a src path (1 level non-recursive)."""
    try:
        for item in os.listdir(src):
            if item.startswith("."):
                # no dotfiles
                continue
            if os.path.isdir(os.path.join(src, item)):
                # added some recursion after splitting posts, ideally 1 level depth max
                try:
                    os.mkdir(f"{dest}/{item}")
                    if depth:
                        copy_dirs(
                            src=os.path.join(src, item),
                            dest=os.path.join(dest, item),
                            depth=(depth - 1),
                        )
                except FileExistsError:
                    # this may be acceptable, especially if the dir already exists
                    pass
                except OSError as error:
                    # other errors should be addressed
                    log.error(f"Creation of directory {item} failed, error: {error}")
                    return False
    except OSError as error:
        log.error(f"Access to {src} failed, error: {error}")
        return False
    return True


def copy_statics(src: str, dest: str, statics: list) -> None:
    """Copy any static files, this runs independently of markdown rendering."""
    for item in statics:
        site = item.replace(src, dest)
        for extension in statics[item]:
            files = list_of_files(
                dirname=item, extension=extension, clean_extension=False
            )
            print(item, extension, files)
            for filename in files:
                try:
                    shutil.copy2(src=filename, dst=site)
                    log.info(f"Static file {filename} copied to {dest}")
                    
                except OSError as error:
                    log.error(f"Copy of static file {filename} failed, error: {error}")


def clean_files(path: str, extension: str, target: list | None = None) -> bool:
    """Delete files from [path] with an [extension]."""
    for filename in list_of_files(
        dirname=path, extension=extension, clean_extension=False
    ):
        if (
            target
        ):  # if there are targetted files, when these are not found the cleanup skips
            found = False
            for target_file in target:
                if filename.split("/")[-1] == f"{target_file}.{extension}":
                    log.info(f"found file: {filename} targeted for delete")
                    found = True
                    break
            if not found:
                continue
        try:
            if ".keep" not in filename:
                os.remove(filename)
        except OSError:
            log.error("Site could not be cleaned", exc_info=True)
            return False
    log.info("Site clean!")
    return True


async def async_clean_files(
    path: str, extension: str, target: list | None = None
) -> bool:
    return clean_files(path, extension, target)
