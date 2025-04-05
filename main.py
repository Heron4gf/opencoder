#
from agent import get_agent
from api.agent_runner import AgentRunner
from api.context_handler import get_context
import asyncio

async def main():
    agent = get_agent()
    runner = AgentRunner(agent)
    while(True):
        user_input = input("Ask the agent: ")
        if(user_input == "exit"):
            break
        if(user_input == "context"):
            print(get_context().serialize())
            continue
        final_response = await runner.run(user_input)
        print(final_response)
    

if __name__ == "__main__":
    asyncio.run(main())