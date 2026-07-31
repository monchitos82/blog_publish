import logging
import os
import sys

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

log = logging.getLogger(__name__)


def evaluate_prompt(message: str, system_prompt: str) -> str | None:
    model = None
    result = {}
    output = None
    try:
        model = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "gemma4"),
            base_url=os.getenv(
                "OLLAMA_BASE_URL", "http://host.containers.internal:11434"
            ),
            temperature=0,
        )
    except Exception as error:
        log.error(f"No model was created, error: {error}")
        return

    if model:
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=message)]
        try:
            result = model.invoke(messages)
        except Exception as error:
            log.error(f"No response was given, error: {error}")
            return

        if result and isinstance(result, AIMessage):
            try:
                output = result.content.encode
            except AttributeError as error:
                log.error(f"No AI message was received, error: {error}")
        else:
            log.error(f"Malformed response was received: {result}")
    return output


if __name__ == "__main__":
    filename = sys.argv[1]

    try:
        with open("./base_prompt.md") as b:
            base_prompt = b.read()
    except OSError as error:
        log.error(f"Could not read base prompt, error: {error}")
        base_prompt = "You are a useful expert"

    system_prompt = base_prompt
    try:
        with open(filename) as f:
            content = f.read()
            if content:
                message = (
                    f"for the file {filename}, perform a spellcheck and validate its grammar on its content:",
                    f"=START=\n{content}\n=END=",
                )
                print(
                    evaluate_prompt(
                        message=message,
                        system_prompt=system_prompt,
                    )
                )
    except IOError:
        log.error(f"File {filename} could not be read")
