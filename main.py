#
from api.agent import get_agent
from api.agent_runner import AgentRunner
from api.context_handler import get_context
import asyncio

async def main():
    agent = get_agent()
    runner = AgentRunner(agent, get_context())
    while(True):
        final_response = await runner.run(input("Ask the agent: "))
        print(final_response)
    

if __name__ == "__main__":
    asyncio.run(main())