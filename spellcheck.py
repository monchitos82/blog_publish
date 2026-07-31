import os
import sys

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama

tools = []
agent_prompt = """
You are an assistant that will use tools to help, you will analyze text and reply with facts, without modifying the input or giving an opinion.
Do not include the original text in your reply and make your response as brief as possible
"""

try:
    with open("./base_prompt.md") as b:
        base_prompt = b.read()
except OSError:
    base_prompt = ""


def evaluate(msg: str, tools: list = tools) -> str | None:
    model = None
    agent = None
    result = {}
    output = None
    try:
        model = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "granite4.1:8b"),
            base_url=os.getenv(
                "OLLAMA_BASE_URL", "http://host.containers.internal:11434"
            ),
        )
    except Exception as error:
        print(f"No model was created, error: {error}")
        return

    if model:
        try:
            agent = create_agent(
                model=model,
                tools=tools,
                system_prompt=(base_prompt + "\n" + agent_prompt),
            )
        except Exception as error:
            print(f"No agent was setup for the model, error: {error}")
            return

        if agent:
            try:
                result = agent.invoke(
                    {
                        "messages": [
                            HumanMessage(
                                content=f"please analyze the following content and find spelling and grammar errors: {msg}, do not analyze code snippets and do not suggest editions, just point the errors when they are present"
                            )
                        ]
                    }
                )
            except Exception as error:
                print(f"No response was given, error: {error}")
                return

            if result:
                messages = result.get("messages", [])
                if messages and len(messages) >= 1:
                    if isinstance(messages[1], AIMessage):
                        output = messages[1].content
                    else:
                        print("No AI message was received")
                else:
                    print("Malformed response was received")
    return output


if __name__ == "__main__":
    filename = sys.argv[1]
    try:
        with open(filename) as f:
            content = f.read()
            if content:
                print(evaluate(msg=content))
    except IOError:
        print(f"File {filename} could not be read")
