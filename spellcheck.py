import logging
import sys


log = logging.getLogger(__name__)


if __name__ == "__main__":
    filename = sys.argv[1]

    try:
        with open(filename) as f:
            content = f.read()
            if content:
                print((content))
    except IOError:
        log.error(f"File {filename} could not be read")
