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
                matches = tool.check(content)
                for m in matches:
                    print(m.ruleId)
                    print(m.message)
                    print(m.replacements)
    except IOError:
        log.error(f"File {filename} could not be read")
