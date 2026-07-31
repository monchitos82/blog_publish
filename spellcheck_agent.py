import logging
import os
import subprocess
import sys

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama

log = logging.getLogger(__name__)


@tool
def echo(input: str) -> str | None:
    """Will repeat back its input"""
    return input


tools = [echo]
agent_prompt = """
You are an assistant whose function is to validate content is grammatically correct"
"""

try:
    with open("./base_prompt.md") as b:
        base_prompt = b.read()
except OSError as error:
    log.error(f"Could not read base prompt, error: {error}")
    base_prompt = ""


def evaluate(msg: str, tools: list = tools) -> str | None:
    log.error(msg, tools)
    model = None
    agent = None
    result = {}
    output = None
    try:
        model = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "gemma3n:latest"),
            base_url=os.getenv(
                "OLLAMA_BASE_URL", "http://host.containers.internal:11434"
            ),
        )
    except Exception as error:
        log.error(f"No model was created, error: {error}")
        return

    if model:
        try:
            agent = create_agent(
                model=model,
                tools=tools,
                system_prompt=(base_prompt + "\n" + agent_prompt),
            )
        except Exception as error:
            log.error(f"No agent was setup for the model, error: {error}")
            return

        if agent:
            try:
                result = agent.invoke({"messages": [HumanMessage(content=msg)]})
            except Exception as error:
                log.error(f"No response was given, error: {error}")
                return

            if result:
                messages = result.get("messages", [])
                if messages and len(messages) >= 1:
                    if isinstance(messages[1], AIMessage):
                        output = messages[1].content
                    else:
                        log.error("No AI message was received")
                else:
                    log.error("Malformed response was received")
    return output


if __name__ == "__main__":
    filename = sys.argv[1]
    try:
        with open(filename) as f:
            content = f.read()
            if content:
                message = f"for the file {filename}, if it is a markdown, evaluate its content: {content}"
                log.info(evaluate(msg=message))
    except IOError:
        log.error(f"File {filename} could not be read")
