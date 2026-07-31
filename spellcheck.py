import os

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_ollama import ChatOllama

tools = []


def evaluate(msg: str, tools: list = tools) -> str | None:
    model = None
    agent = None
    result = {}
    output = None
    try:
        model = ChatOllama(model=os.getenv("OLLAMA_MODEL", "granite4.1:8b"))
    except Exception:
        print("No model was created")
        return

    if model:
        try:
            agent = create_agent(
                model=model,
                tools=tools,
                system_prompt="You are an assistant that will use tools to help, you will analyze text and reply with facts, without modifying the input or giving an opinion",
            )
        except Exception:
            print("No agent was setup for the model")
            return

        if agent:
            try:
                result = agent.invoke(
                    {
                        "messages": [
                            HumanMessage(
                                content=f"please analyze the following text and find spelling and grammar errors: {msg}"
                            )
                        ]
                    }
                )
            except Exception:
                print("No response was given")
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
