import logging
import os
import sys

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
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
        try:
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    ("human", "{message}"),
                ]
            )
            chain = prompt | model
        except Exception as error:
            log.error(f"No agent was setup for the model, error: {error}")
            return

        if chain:
            try:
                result = chain.invoke({"message": message})
            except Exception as error:
                log.error(f"No response was given, error: {error}")
                return

            if result:
                messages = result.get("messages", [])
                if messages and len(messages) >= 1:
                    for message_ in messages:
                        if isinstance(message_, AIMessage):
                            output = message_.content
                            return output
                    if not output:
                        log.error(f"No AI message was received: {messages}")
                else:
                    log.error(f"Malformed response was received: {result}")
    return output


if __name__ == "__main__":
    filename = sys.argv[1]

    action_prompt = """
    You are an assistant whose function is to validate content is grammatically correct"
    """

    try:
        with open("./base_prompt.md") as b:
            base_prompt = b.read()
    except OSError as error:
        log.error(f"Could not read base prompt, error: {error}")
        base_prompt = ""

    system_prompt = base_prompt + "\n" + action_prompt
    try:
        with open(filename) as f:
            content = f.read()
            if content:
                message = f"for the file {filename}, if it is a markdown, evaluate if it is grammatically correct: {content}"
                print(
                    evaluate_prompt(
                        message=message,
                        system_prompt=system_prompt,
                    )
                )
    except IOError:
        log.error(f"File {filename} could not be read")
