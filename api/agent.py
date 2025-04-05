# api/agent.py
from load_client import get_client
from agents import Agent, OpenAIChatCompletionsModel
import os
from dotenv import load_dotenv
from tools import get_tools

def get_model():
    load_dotenv
    return os.getenv("MODEL")

def get_agent(tools = get_tools(), selected_model = get_model()):
    agent = Agent(
        name = "Coder Agent",
        instructions="You're a helpful code agent with file management and shell tools",
        model=OpenAIChatCompletionsModel(
            model=selected_model,
            openai_client=get_client()
        ),
        tools=tools,
    )
    return agent

