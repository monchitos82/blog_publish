import os
import sys

import logging

from neocitizen import NeocitiesApi, ApiError

log = logging.getLogger(__name__)


def upload_site(api_key: str = "", dest: str = "./site") -> bool:
    """Upload the site to neocities."""
    result = False
    try:
        api = NeocitiesApi(api_key=api_key)
        api.upload_dir(dest)
    except ApiError as error:
        log.error(f"Failed to upload site {dest}, error: {error}")
    else:
        result = True
    return result

if __name__ == "__main__":
    api_key = os.getenv("NEOCITIES_API_KEY", None)
    if api_key:
        if upload_site(api_key=api_key):
            log.info("Upload complete!")
    else:
        log.error("No API key has been defined")
        sys.exit(1)
    sys.exit(0)
