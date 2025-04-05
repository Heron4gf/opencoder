# api/agent_runner.py
from agents import Runner
from .context_handler import get_context


class AgentRunner():
    def __init__(self, agent):
        self.agent = agent

    async def run(self, input) -> str:
        get_context().add_user_message(input)
        response = await Runner.run(starting_agent=self.agent, input=get_context().serialize())
        final_output = response.final_output.strip()
        get_context().add_system_message(final_output)
        return final_output