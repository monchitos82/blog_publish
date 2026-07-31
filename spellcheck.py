import logging
import sys
import language_tool_python


log = logging.getLogger(__name__)


if __name__ == "__main__":
    filename = sys.argv[1]

    try:
        with open(filename) as f:
            content = f.read()
            if content:
                tool = language_tool_python.LanguageTool("en-US")
                results = tool.check(content)
                for match in results:
                    log.warning(match.rule_id)
                    print(match.message)
                    print(match.replacements)
                    print("")
    except IOError:
        log.error(f"File {filename} could not be read")
