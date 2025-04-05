# api/agent.py
from load_client import get_client
from agents import Agent, OpenAIChatCompletionsModel
import os
from dotenv import load_dotenv
from tools import get_tools

def get_default_prompt():
    with open("default_prompt.md", "r") as file:
        content = file.read()
    return(content)

def get_model():
    model = "google/gemini-2.5-pro-exp-03-25:free"
    print("Selected model: "+model)
    return model

def get_agent(tools = get_tools(), selected_model = get_model()):
    agent = Agent(
        name = "Coder Agent",
        instructions=get_default_prompt(),
        model=OpenAIChatCompletionsModel(
            model=selected_model,
            openai_client=get_client()
        ),
        tools=tools,
    )
    return agent

